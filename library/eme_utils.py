#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import re
import os

def run_air_command(module, command):
    """Run an air command and return the result.
    
    Args:
        module: Ansible module instance
        command: Command to execute
        
    Returns:
        tuple: (return_code, stdout, stderr, command)
    """
    try:
        # Get Ab Initio environment from module parameters
        ab_env = module.params.get('ab_env', {})
        
        # Ensure we have a clean environment
        env = os.environ.copy()
        if ab_env:
            env.update(ab_env)
        
        # Split the command into a list for safer execution
        cmd_parts = command.split()
        
        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env
        )
        stdout, stderr = process.communicate()
            
        return process.returncode, stdout, stderr, command
    except Exception as e:
        module.fail_json(
            msg="Failed to execute air command: {}".format(str(e)),
            cmd=command
        )

def parse_tag_objects(output):
    """Parse the output of 'air tag show' command into a structured format."""
    objects = []
    # Pattern: one or more digits followed by whitespace and a path starting with /
    pattern = r'^\s*(\d+)\s+(/.*)$'
    
    for line in output.splitlines():
        match = re.match(pattern, line)
        if match:
            version, path = match.groups()
            objects.append({
                'path': path.strip(),
                'version': version
            })
    return objects

def get_tag_objects(module, tag_name):
    """Get objects associated with a tag."""
    command = "air tag show {} -objects -verbose".format(tag_name)
    return run_air_command(module, command)

def check_object_exists(module, obj_path, version_path):
    """Check if an object exists with the specified version."""
    command = "air object exists '{}' -version '{}'".format(obj_path, version_path)
    return run_air_command(module, command)

def check_tag_exists(module, tag_name):
    """Check if a tag exists and return detailed information."""
    command = "ls -l /tmp/{}".format(tag_name)
    return run_air_command(module, command)

def export_object(module, obj_path, version_path, output_file):
    """Export an object to an ARL file."""
    command = "air object export '{}' -version '{}' -file {}".format(obj_path, version_path, output_file)
    return run_air_command(module, command)

def import_object(module, arl_file):
    """Import an object from an ARL file."""
    command = "air object import {}".format(arl_file)
    return run_air_command(module, command)

def export_tag(module, tag_name, output_file):
    """Export a tag with its objects to an ARL file."""
    command = "air object export /EMETags/{} -file {} -with-objects".format(tag_name, output_file)
    return run_air_command(module, command)

def create_tag(module, tag_name, objects, comment):
    """Create a new tag with specified objects."""
    if not tag_name:
        module.fail_json(msg="tag_name is required for create_tag action")
    if not objects:
        module.fail_json(msg="objects is required for create_tag action")

    # Format objects for air tag create command
    object_list = []
    for obj in objects:
        object_list.append("{}({})".format(obj['path'], obj['version']))
    
    object_string = " ".join(object_list)
    if comment:
        object_string += " -comment {}".format(comment)

    # Build the air tag create command
    command = "air tag create {} -exact -objects {}".format(tag_name, object_string)
    return run_air_command(module, command)

def get_air_version(module):
    """Get the version of the air CLI."""
    command = "air version"
    return run_air_command(module, command)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True, choices=[
                'get_tag_objects',
                'check_object',
                'check_tag',
                'export_object',
                'import_object',
                'export_tag',
                'create_tag',
                'get_air_version'
            ]),
            tag_name=dict(type='str', required=False),
            object_path=dict(type='str', required=False),
            version_path=dict(type='str', required=False),
            output_file=dict(type='str', required=False),
            arl_file=dict(type='str', required=False),
            comment=dict(type='str', required=False),
            ab_env=dict(type='dict', required=False, default={})
        ),
        required_if=[
            ('action', 'get_tag_objects', ['tag_name']),
            ('action', 'check_object', ['object_path', 'version_path']),
            ('action', 'check_tag', ['tag_name']),
            ('action', 'export_object', ['object_path', 'version_path', 'output_file']),
            ('action', 'import_object', ['arl_file']),
            ('action', 'export_tag', ['tag_name', 'output_file']),
            ('action', 'create_tag', ['tag_name', 'objects'])
        ]
    )

    action = module.params['action']
    result = dict(changed=False)

    try:
        if action == 'get_tag_objects':
            rc, stdout, stderr, cmd = get_tag_objects(module, module.params['tag_name'])
            if rc != 0:
                module.fail_json(msg="Failed to get tag objects: {}".format(stderr))
            objects = parse_tag_objects(stdout)
            result['objects'] = objects
            result['count'] = len(objects)
        elif action == 'check_object':
            rc, stdout, stderr, cmd = check_object_exists(
                module,
                module.params['object_path'],
                module.params['version_path']
            )
            result['exists'] = rc == 0
            result['details'] = {
                'return_code': rc,
                'stdout': stdout,
                'stderr': stderr,
                'command': cmd
            }
        elif action == 'check_tag':
            rc, stdout, stderr, cmd = check_tag_exists(module, module.params['tag_name'])
            result['exists'] = rc == 0
            result['details'] = {
                'return_code': rc,
                'stdout': stdout,
                'stderr': stderr,
                'command': cmd
            }
            if not result['exists']:
                result['message'] = "Tag does not exist and can be created"
        elif action == 'export_object':
            rc, stdout, stderr, cmd = export_object(
                module,
                module.params['object_path'],
                module.params['version_path'],
                module.params['output_file']
            )
            if rc != 0:
                module.fail_json(msg="Failed to export object: {}".format(stderr))
            result['changed'] = True
        elif action == 'import_object':
            rc, stdout, stderr, cmd = import_object(module, module.params['arl_file'])
            if rc != 0:
                module.fail_json(msg="Failed to import object: {}".format(stderr))
            result['changed'] = True
        elif action == 'export_tag':
            rc, stdout, stderr, cmd = export_tag(
                module,
                module.params['tag_name'],
                module.params['output_file']
            )
            if rc != 0:
                module.fail_json(msg="Failed to export tag: {}".format(stderr))
            result['changed'] = True
        elif action == 'create_tag':
            rc, stdout, stderr, cmd = create_tag(
                module,
                module.params['tag_name'],
                get_tag_objects(module, module.params['tag_name']),
                module.params['comment']
            )
            if rc != 0:
                module.fail_json(msg="Failed to create tag: {}".format(stderr))
            result['changed'] = True
        elif action == 'get_air_version':
            rc, stdout, stderr, cmd = get_air_version(module)
            if rc != 0:
                module.fail_json(msg="Failed to get air version: {}".format(stderr))
            result['version'] = stdout.strip()

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main() 