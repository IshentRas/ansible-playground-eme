#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import re
import os

def run_air_command(module, command):
    """Run an air command and return the result."""
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
        
        if process.returncode != 0:
            module.fail_json(
                msg=f"Command failed with return code {process.returncode}",
                stdout=stdout,
                stderr=stderr,
                cmd=command
            )
            
        return process.returncode, stdout, stderr
    except Exception as e:
        module.fail_json(
            msg=f"Failed to execute air command: {str(e)}",
            cmd=command
        )

def parse_tag_objects(output):
    """Parse the output of 'air tag show' command into a structured format."""
    objects = []
    for line in output.splitlines():
        # Strip whitespace and check if line contains an object path
        line = line.strip()
        if '/' in line:
            # Extract object path and version
            match = re.match(r'^(.*?)\((.*?)\)$', line)
            if match:
                obj_path, version_path = match.groups()
                objects.append({
                    'path': obj_path,
                    'version': version_path
                })
    return objects

def get_tag_objects(module, tag_name):
    """Get objects associated with a tag."""
    command = f"air tag show {tag_name} -objects -verbose"
    rc, stdout, stderr = run_air_command(module, command)
    
    if rc != 0:
        module.fail_json(msg=f"Failed to get tag objects: {stderr}")
    
    return parse_tag_objects(stdout)

def check_object_exists(module, obj_path, version_path):
    """Check if an object exists with the specified version."""
    command = f"air object exists '{obj_path}' -version '{version_path}'"
    rc, stdout, stderr = run_air_command(module, command)
    return rc == 0

def check_tag_exists(module, tag_name):
    """Check if a tag exists."""
    command = f"air tag show {tag_name}"
    rc, stdout, stderr = run_air_command(module, command)
    return rc == 0

def export_object(module, obj_path, version_path, output_file):
    """Export an object to an ARL file."""
    command = f"air object export '{obj_path}' -version '{version_path}' -file {output_file}"
    rc, stdout, stderr = run_air_command(module, command)
    if rc != 0:
        module.fail_json(msg=f"Failed to export object: {stderr}")
    return True

def import_object(module, arl_file):
    """Import an object from an ARL file."""
    command = f"air object import {arl_file}"
    rc, stdout, stderr = run_air_command(module, command)
    if rc != 0:
        module.fail_json(msg=f"Failed to import object: {stderr}")
    return True

def export_tag(module, tag_name, output_file):
    """Export a tag with its objects to an ARL file."""
    command = f"air object export /EMETags/{tag_name} -file {output_file} -with-objects"
    rc, stdout, stderr = run_air_command(module, command)
    if rc != 0:
        module.fail_json(msg=f"Failed to export tag: {stderr}")
    return True

def create_tag(module, tag_name, objects, comment):
    """Create a new tag with specified objects."""
    if not tag_name:
        module.fail_json(msg="tag_name is required for create_tag action")
    if not objects:
        module.fail_json(msg="objects is required for create_tag action")

    # Format objects for air tag create command
    object_list = []
    for obj in objects:
        object_list.append(f"{obj['path']}({obj['version']})")
    
    object_string = " ".join(object_list)
    if comment:
        object_string += f" -comment {comment}"

    # Build the air tag create command
    cmd = ['air', 'tag', 'create', tag_name, '-exact', '-objects', object_string]

    # Execute the command
    rc, out, err = run_air_command(module, ' '.join(cmd))
    if rc != 0:
        module.fail_json(msg=f"Failed to create tag: {err}")

    return True

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
                'create_tag'
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
            objects = get_tag_objects(module, module.params['tag_name'])
            result['objects'] = objects
            result['count'] = len(objects)
        elif action == 'check_object':
            exists = check_object_exists(
                module,
                module.params['object_path'],
                module.params['version_path']
            )
            result['exists'] = exists
        elif action == 'check_tag':
            exists = check_tag_exists(module, module.params['tag_name'])
            result['exists'] = exists
        elif action == 'export_object':
            success = export_object(
                module,
                module.params['object_path'],
                module.params['version_path'],
                module.params['output_file']
            )
            result['changed'] = success
        elif action == 'import_object':
            success = import_object(module, module.params['arl_file'])
            result['changed'] = success
        elif action == 'export_tag':
            success = export_tag(
                module,
                module.params['tag_name'],
                module.params['output_file']
            )
            result['changed'] = success
        elif action == 'create_tag':
            success = create_tag(
                module,
                module.params['tag_name'],
                get_tag_objects(module, module.params['tag_name']),
                module.params['comment']
            )
            result['changed'] = success

        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main() 