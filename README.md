# EME Release Management with Ansible

This project provides Ansible playbooks for managing EME (Enterprise Metadata Environment) releases and promotions.

## Prerequisites

- Ansible 2.9 or higher
- Access to EME servers
- Python 3.x
- Ab Initio `air` command-line tool installed on EME servers

## Project Structure

```
.
├── create_release_tag.yml      # Playbook for creating a release tag from feature tags
├── promote_release.yml         # Playbook for promoting a release tag between environments
├── library/
│   └── eme_utils.py           # Custom module for EME operations
└── roles/
    ├── eme_common/            # Common tasks and handlers
    ├── eme_release_creation/  # Tasks for creating release tags
    ├── eme_verification/      # Tasks for verifying EME objects and tags
    └── eme_promotion/         # Tasks for promoting releases between environments
```

## Creating a Release Tag

The `create_release_tag.yml` playbook creates a new release tag by combining objects from multiple feature tags in a lower environment (SIT or UAT).

### Usage

```bash
ansible-playbook create_release_tag.yml
```

The playbook will prompt for:
- Release tag name
- Feature tag names (comma-separated)
- Source environment (SIT or UAT only)
- Debug output option (yes/no)

### Process

1. Creates a release tag in the specified lower environment (SIT or UAT)
2. Combines objects from all specified feature tags
3. Removes exact duplicates while preserving unique object-version combinations
4. Provides debug output if enabled

## Promoting a Release

The `promote_release.yml` playbook promotes a release tag from one environment to another, handling dependencies and object versions.

### Usage

```bash
ansible-playbook promote_release.yml
```

The playbook will prompt for:
- Source environment (SIT, UAT, or pre-prod)
- Release tag name
- Target environment (UAT, pre-prod, or prod)
- Debug output option (yes/no)

### Process

1. Verifies the release tag exists in the source environment
2. Checks for missing objects in the target environment
3. Exports missing objects from source EME server
4. Transfers ARL files through control node to target EME server
5. Imports objects into target EME server
6. Creates the release tag in the target environment
7. Provides debug output if enabled

### Host Targeting

The promotion playbook:
- Uses direct host names (e.g., 'eme-sit', 'eme-uat') for targeting servers
- Runs tasks on both source and target EME servers
- Delegates specific tasks to the appropriate servers using host variables
- Maintains proper file transfer sequence through the control node
- Defaults to 'sit' for source and 'uat' for target if not specified

## Environment Flow

Release tags should follow this promotion path:
1. Created in SIT or UAT
2. Promoted to UAT (if created in SIT)
3. Promoted to pre-prod
4. Promoted to prod

## Debug Output

Debug output can be enabled for both playbooks to provide detailed information about:
- Object verification results
- Export/import progress
- Tag creation status
- Missing objects and dependencies

## Custom Module

The `eme_utils.py` module provides the following actions:
- `check_tag`: Verify if a tag exists
- `get_tag_objects`: Get objects from a tag
- `check_object`: Check if an object exists
- `export_object`: Export an object to ARL file
- `import_object`: Import an object from ARL file
- `create_tag`: Create a new tag
- `export_tag`: Export a tag to ARL file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 