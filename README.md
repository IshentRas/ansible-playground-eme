# Ab Initio EME Release Promotion

This Ansible project automates the promotion of Ab Initio EME releases across different environments (DEV, SIT, UAT, PRE-PROD, PROD). It ensures consistent and reliable promotion of application releases while maintaining proper version control and environment isolation.

## Prerequisites

- Ansible Automation Platform (AAP) or Ansible Core
- Access to source and target EME environments
- Proper permissions to execute EME commands
- SSH access to EME servers

## Directory Structure

```
.
├── inventory/
│   └── hosts.yml           # Environment inventory
├── library/
│   └── eme_utils.py        # Custom EME operations module
├── roles/
│   ├── eme_common/         # Common tasks and handlers
│   │   ├── handlers/
│   │   │   └── main.yml    # Cleanup handlers
│   │   └── tasks/
│   │       └── main.yml    # Common setup tasks
│   ├── eme_verification/   # Pre-promotion checks
│   │   └── tasks/
│   │       └── main.yml    # Verification tasks
│   ├── eme_promotion/      # Promotion operations
│   │   └── tasks/
│   │       └── main.yml    # Promotion tasks
│   └── eme_release_creation/ # Release tag creation
│       └── tasks/
│           └── main.yml    # Tag creation tasks
├── promote_release.yml     # Main promotion playbook
└── create_release_tag.yml  # Release tag creation playbook
```

## Usage

### Command Line Usage

#### Creating a Release Tag

1. Run the release tag creation playbook:
   ```bash
   ansible-playbook create_release_tag.yml
   ```

2. When prompted, provide:
   - Release tag name (e.g., release-candidate-1.0)
   - Feature tags to include (comma-separated list)
   - Debug output (yes/no)

The playbook will:
- Execute on the SIT environment
- Collect objects from all specified feature tags
- Preserve all unique object-version combinations:
  - If the same object appears with different versions in different feature tags, all versions are kept
  - Only exact duplicates (same object with same version) are removed
- Create a new release tag with the combined objects
- Display information about the created tag (if debug is enabled)

Debug Output:
- When enabled, displays:
  - Number of objects in the created tag
  - Detailed list of all objects and their versions
- Useful for:
  - Verifying object versions from different feature tags
  - Troubleshooting tag creation issues
  - Auditing release content

#### Promoting a Release

1. Update the inventory file with your environment details:
   ```yaml
   all:
     children:
       sit:
         hosts:
           sit-eme:
             ansible_host: sit-eme-server
       uat:
         hosts:
           uat-eme:
             ansible_host: uat-eme-server
       # ... other environments
   ```

2. Run the playbook:
   ```bash
   ansible-playbook promote_release.yml
   ```

3. When prompted, provide:
   - Source environment (e.g., sit, uat, pre-prod)
   - Release tag name to promote
   - Target environment (e.g., uat, pre-prod, prod)
   - Debug output (yes/no)

Debug Output:
- When enabled, displays:
  - Verification results and missing objects
  - Object export and import progress
  - Promotion start and completion status
- Useful for:
  - Monitoring promotion progress
  - Troubleshooting issues
  - Auditing promotion operations

### Ansible Automation Platform (AAP) Usage

#### Creating a Release Tag

1. Create a job template using the `create_release_tag.yml` playbook

2. Configure survey questions in the job template:
   ```yaml
   spec:
     - question_name: "Release Tag Name"
       question_description: "Enter the release tag name (e.g., release-candidate-1.0)"
       variable: "release_tag"
       type: "text"
       required: true

     - question_name: "Feature Tags"
       question_description: "Enter the feature tags to include (comma-separated)"
       variable: "feature_tags"
       type: "textarea"
       required: true

     - question_name: "Debug Output"
       question_description: "Enable detailed debug output?"
       variable: "debug_mode"
       type: "multiplechoice"
       choices:
         - "yes"
         - "no"
       default: "no"
   ```

Note: Release tags are always created in the SIT environment, so no environment selection is needed.

#### Promoting a Release

1. Create a new project in AAP and sync this repository

2. Create a job template using the `promote_release.yml` playbook

3. Configure survey questions in the job template with predefined choices:
   ```yaml
   spec:
     - question_name: "Source Environment"
       question_description: "Select the source environment"
       variable: "source_env"
       type: "multiplechoice"
       choices:
         - "dev"
         - "sit"
         - "uat"
         - "pre-prod"
       required: true

     - question_name: "Target Environment"
       question_description: "Select the target environment"
       variable: "target_env"
       type: "multiplechoice"
       choices:
         - "sit"
         - "uat"
         - "pre-prod"
         - "prod"
       required: true

     - question_name: "Release Tag"
       question_description: "Enter the release tag to promote"
       variable: "release_tag"
       type: "text"
       required: true

     - question_name: "Debug Output"
       question_description: "Enable detailed debug output?"
       variable: "debug_mode"
       type: "multiplechoice"
       choices:
         - "yes"
         - "no"
       default: "no"
   ```

4. The survey will create a form in the AAP web interface with:
   - Dropdown menus for source and target environments
   - Text input for the release tag
   - Validation to ensure proper promotion path

5. Run the job template from the AAP web interface

Note: When running in AAP, variables must be provided through the job template configuration rather than through interactive prompts. The survey questions provide a user-friendly interface for selecting environments and entering the release tag.

## Process Flow

1. **Release Tag Creation**
   - Collects objects from multiple feature tags
   - Combines and deduplicates objects
   - Creates a new release tag with exact versions
   - Provides detailed information about the created tag

2. **Environment Validation**
   - Validates environment names and promotion path
   - Creates temporary directories
   - Verifies EME connectivity

3. **Object Verification**
   - Checks if release tag already exists in target (fails if it does)
   - Retrieves objects associated with the release tag
   - Verifies object versions in target environment
   - Identifies missing objects

4. **Release Promotion**
   - Exports missing objects from source EME
   - Transfers ARL files through control node
   - Imports objects into target EME
   - Exports and imports release tag
   - Cleans up temporary files

## Custom Module

The project includes a custom Python module (`eme_utils.py`) that encapsulates EME operations:

- `get_tag_objects`: Retrieves objects associated with a tag
- `check_object`: Verifies object existence
- `check_tag`: Verifies tag existence
- `export_object`: Exports object to ARL
- `import_object`: Imports object from ARL
- `export_tag`: Exports tag with objects

## Error Handling

- Fails early if release tag already exists in target
- Proper cleanup of temporary files on failure
- Detailed error messages for troubleshooting
- Handlers ensure cleanup even on early failures

## Best Practices

1. **Release Tag Management**
   - Create new, immutable release tags
   - Never reuse existing tags
   - Use consistent naming conventions

2. **Environment Promotion**
   - Follow the defined promotion path
   - Verify objects before promotion
   - Clean up temporary files after completion

3. **Error Handling**
   - Check for existing tags before promotion
   - Maintain temporary files for investigation on failure
   - Use handlers for reliable cleanup

## Troubleshooting

1. **Tag Already Exists**
   - Create a new release tag
   - Ensure proper versioning

2. **Missing Objects**
   - Verify object paths
   - Check EME connectivity
   - Ensure proper permissions

3. **Import Failures**
   - Check ARL file integrity
   - Verify target EME space
   - Review EME logs

## Security Considerations

- Use AAP credentials for secure execution
- Implement proper access controls
- Follow least privilege principle
- Secure temporary file handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Your License Here] 