import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any
from pathlib import Path
import readline  # For better input experience

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parents[1]))
from profile_manager import ProfileManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

class ProfileManagerCLI:
    """Command-line interface for managing gesture profiles"""
    
    COMMANDS = [
        "list", "create", "clone", "edit", "delete", "activate", 
        "export", "import", "help", "exit"
    ]
    
    def __init__(self):
        """Initialize the CLI with a profile manager"""
        self.profile_manager = ProfileManager()
        self.active_profile_id = self.profile_manager.active_profile
        self.username = os.getenv("USER", "user")
        self.profile_manager.username = self.username
        
        # Set up command completion
        readline.set_completer(self.completer)
        readline.parse_and_bind("tab: complete")
    
    def completer(self, text, state):
        """Tab completion for commands"""
        options = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    
    def run_interactive(self):
        """Run the CLI in interactive mode"""
        print("\n" + "="*60)
        print("  GestureDrive Profile Manager CLI")
        print("="*60)
        print("Type 'help' for a list of commands or 'exit' to quit.\n")
        
        while True:
            try:
                command = input("profile-manager> ").strip()
                if not command:
                    continue
                
                if command == "exit":
                    print("Goodbye!")
                    break
                
                self.parse_command(command)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def run_command(self, args):
        """Run a single command from command line arguments"""
        parser = argparse.ArgumentParser(description="GestureDrive Profile Manager CLI")
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # List command
        list_parser = subparsers.add_parser("list", help="List available profiles")
        
        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new profile")
        create_parser.add_argument("name", help="Name for the new profile")
        create_parser.add_argument("--description", "-d", help="Profile description")
        create_parser.add_argument("--base", "-b", default="default", 
                                   help="Base profile ID (default: 'default')")
        create_parser.add_argument("--personal", "-p", action="store_true", 
                                   help="Create as a personal profile")
        
        # Clone command
        clone_parser = subparsers.add_parser("clone", help="Clone an existing profile")
        clone_parser.add_argument("source", help="Source profile ID")
        clone_parser.add_argument("name", help="Name for the cloned profile")
        clone_parser.add_argument("--description", "-d", help="Profile description")
        clone_parser.add_argument("--personal", "-p", action="store_true", 
                                 help="Create as a personal profile")
        
        # Activate command
        activate_parser = subparsers.add_parser("activate", help="Activate a profile")
        activate_parser.add_argument("profile_id", help="ID of the profile to activate")
        
        # Delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a profile")
        delete_parser.add_argument("profile_id", help="ID of the profile to delete")
        delete_parser.add_argument("--force", "-f", action="store_true", 
                                  help="Skip confirmation")
        
        # Export command
        export_parser = subparsers.add_parser("export", help="Export a profile to a file")
        export_parser.add_argument("profile_id", help="ID of the profile to export")
        export_parser.add_argument("output_path", help="Path to save the export")
        
        # Import command
        import_parser = subparsers.add_parser("import", help="Import a profile from a file")
        import_parser.add_argument("input_path", help="Path to the profile file")
        import_parser.add_argument("--name", "-n", help="New name for the profile")
        import_parser.add_argument("--personal", "-p", action="store_true", 
                                  help="Import as a personal profile")
        
        # Parse the arguments
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
            
        # Execute the command
        {
            "list": self.cmd_list,
            "create": self.cmd_create,
            "clone": self.cmd_clone,
            "activate": self.cmd_activate,
            "delete": self.cmd_delete,
            "export": self.cmd_export,
            "import": self.cmd_import,
            "help": self.cmd_help
        }.get(parsed_args.command, lambda x: parser.print_help())(parsed_args)
    
    def parse_command(self, command_line):
        """Parse a command from the interactive CLI"""
        parts = command_line.split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:]
        
        if command == "list":
            self.cmd_list_interactive()
        elif command == "create":
            self.cmd_create_interactive(args)
        elif command == "clone":
            self.cmd_clone_interactive(args)
        elif command == "edit":
            self.cmd_edit_interactive(args)
        elif command == "delete":
            self.cmd_delete_interactive(args)
        elif command == "activate":
            self.cmd_activate_interactive(args)
        elif command == "export":
            self.cmd_export_interactive(args)
        elif command == "import":
            self.cmd_import_interactive(args)
        elif command == "help":
            self.cmd_help_interactive()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Type 'help' for a list of commands.")
    
    def cmd_list_interactive(self):
        """List available profiles (interactive mode)"""
        self.profile_manager.refresh_available_profiles()
        profiles = self.profile_manager.available_profiles
        
        if not profiles:
            logger.info("No profiles available.")
            return
            
        # Group profiles by type
        system_profiles = [p for p in profiles if p["type"] == "system"]
        shared_profiles = [p for p in profiles if p["type"] == "shared"]
        user_profiles = [p for p in profiles if p["type"] == "user"]
        
        # Print profiles
        print("\nAvailable Profiles:")
        print("-" * 80)
        
        if system_profiles:
            print("\nSystem Profiles:")
            self._print_profile_list(system_profiles)
            
        if shared_profiles:
            print("\nShared Profiles:")
            self._print_profile_list(shared_profiles)
            
        if user_profiles:
            print("\nYour Profiles:")
            self._print_profile_list(user_profiles)
            
        print("-" * 80)
        print(f"Active Profile: {self.active_profile_id}")
        print("-" * 80)
    
    def _print_profile_list(self, profiles):
        """Print a formatted list of profiles"""
        for profile in profiles:
            active_marker = "*" if profile["id"] == self.active_profile_id else " "
            print(f"{active_marker} {profile['id']:<20} | {profile['name']:<30} | "
                  f"{profile['author']}")
    
    def cmd_create_interactive(self, args):
        """Create a new profile (interactive mode)"""
        if args and len(args) >= 1:
            # Arguments provided: name [description] [base_profile] [personal]
            name = args[0]
            description = args[1] if len(args) > 1 else ""
            base_profile = args[2] if len(args) > 2 else "default"
            personal = args[3] == "personal" if len(args) > 3 else False
        else:
            # No arguments, prompt for input
            name = input("Profile name: ").strip()
            description = input("Description (optional): ").strip()
            base_profile = input("Base profile ID (default: 'default'): ").strip() or "default"
            personal = input("Create as personal profile? (y/n): ").lower() == "y"
            
        # Validate inputs
        if not name:
            logger.error("Profile name is required.")
            return
            
        # Create the profile
        profile_id = self.profile_manager.create_new_profile(
            name=name, 
            description=description, 
            as_user_profile=personal
        )
        
        if profile_id:
            logger.info(f"Profile created successfully: {profile_id}")
        else:
            logger.error("Failed to create profile.")
    
    def cmd_clone_interactive(self, args):
        """Clone an existing profile (interactive mode)"""
        if args and len(args) >= 2:
            # Arguments provided: source_id name [description] [personal]
            source_id = args[0]
            name = args[1]
            description = args[2] if len(args) > 2 else ""
            personal = args[3] == "personal" if len(args) > 3 else False
        else:
            # First, list available profiles
            self.cmd_list_interactive()
            
            # Prompt for input
            source_id = input("Source profile ID: ").strip()
            name = input("New profile name: ").strip()
            description = input("Description (optional): ").strip()
            personal = input("Create as personal profile? (y/n): ").lower() == "y"
            
        # Validate inputs
        if not source_id or not name:
            logger.error("Source profile ID and name are required.")
            return
            
        # Clone the profile
        profile_id = self.profile_manager.clone_profile(
            profile_id=source_id, 
            new_name=name, 
            as_user_profile=personal
        )
        
        if profile_id:
            logger.info(f"Profile cloned successfully: {profile_id}")
        else:
            logger.error("Failed to clone profile.")
    
    def cmd_edit_interactive(self, args):
        """Edit an existing profile (interactive mode)"""
        # This is a simplified version - in a real implementation,
        # you might want to use a text editor to edit the profile JSON
        
        if args and len(args) >= 1:
            profile_id = args[0]
        else:
            # List available profiles
            self.cmd_list_interactive()
            profile_id = input("Profile ID to edit: ").strip()
            
        if not profile_id:
            logger.error("Profile ID is required.")
            return
            
        # Get the profile
        profile_info = self.profile_manager.get_profile_info(profile_id)
        if not profile_info:
            logger.error(f"Profile not found: {profile_id}")
            return
            
        if profile_id == "default":
            logger.error("Cannot edit the default profile.")
            return
            
        # Load the profile data
        try:
            with open(profile_info["path"], 'r') as f:
                profile_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return
            
        # Prompt for edits
        print(f"\nEditing profile: {profile_info['name']}")
        new_name = input(f"New name (current: {profile_info['name']}): ").strip() or profile_info['name']
        new_description = input(f"New description (current: {profile_info.get('description', '')}): ").strip() or profile_info.get('description', '')
        
        # Update the profile data
        profile_data["profileName"] = new_name
        profile_data["description"] = new_description
        
        # Save the updated profile
        result = self.profile_manager.save_profile(profile_data, profile_id, overwrite=True)
        if result:
            logger.info(f"Profile updated successfully: {result}")
        else:
            logger.error("Failed to update profile.")
    
    def cmd_delete_interactive(self, args):
        """Delete a profile (interactive mode)"""
        if args and len(args) >= 1:
            profile_id = args[0]
            force = len(args) > 1 and args[1] == "--force"
        else:
            # List available profiles
            self.cmd_list_interactive()
            profile_id = input("Profile ID to delete: ").strip()
            force = False
            
        if not profile_id:
            logger.error("Profile ID is required.")
            return
            
        if profile_id == "default":
            logger.error("Cannot delete the default profile.")
            return
            
        # Get the profile
        profile_info = self.profile_manager.get_profile_info(profile_id)
        if not profile_info:
            logger.error(f"Profile not found: {profile_id}")
            return
            
        # Confirm deletion
        if not force:
            confirm = input(f"Are you sure you want to delete the profile '{profile_info['name']}'? (y/n): ")
            if confirm.lower() != "y":
                logger.info("Deletion cancelled.")
                return
                
        # Delete the profile
        if self.profile_manager.delete_profile(profile_id):
            logger.info(f"Profile deleted successfully: {profile_id}")
        else:
            logger.error("Failed to delete profile.")
    
    def cmd_activate_interactive(self, args):
        """Activate a profile (interactive mode)"""
        if args and len(args) >= 1:
            profile_id = args[0]
        else:
            # List available profiles
            self.cmd_list_interactive()
            profile_id = input("Profile ID to activate: ").strip()
            
        if not profile_id:
            logger.error("Profile ID is required.")
            return
            
        # Activate the profile
        if self.profile_manager.load_profile(profile_id):
            self.active_profile_id = profile_id
            logger.info(f"Profile activated successfully: {profile_id}")
        else:
            logger.error("Failed to activate profile.")
    
    def cmd_export_interactive(self, args):
        """Export a profile to a file (interactive mode)"""
        if args and len(args) >= 2:
            profile_id = args[0]
            output_path = args[1]
        else:
            # List available profiles
            self.cmd_list_interactive()
            profile_id = input("Profile ID to export: ").strip()
            output_path = input("Output file path: ").strip()
            
        if not profile_id or not output_path:
            logger.error("Profile ID and output path are required.")
            return
            
        # Export the profile
        if self.profile_manager.export_profile(profile_id, output_path):
            logger.info(f"Profile exported successfully to {output_path}")
        else:
            logger.error("Failed to export profile.")
    
    def cmd_import_interactive(self, args):
        """Import a profile from a file (interactive mode)"""
        if args and len(args) >= 1:
            input_path = args[0]
            new_name = args[1] if len(args) > 1 else None
            personal = args[2] == "personal" if len(args) > 2 else False
        else:
            input_path = input("Path to profile file: ").strip()
            new_name = input("New name (optional): ").strip() or None
            personal = input("Import as personal profile? (y/n): ").lower() == "y"
            
        if not input_path:
            logger.error("Profile file path is required.")
            return
            
        # Import the profile
        profile_id = self.profile_manager.import_profile(
            import_path=input_path, 
            new_name=new_name, 
            as_user_profile=personal
        )
        
        if profile_id:
            logger.info(f"Profile imported successfully: {profile_id}")
        else:
            logger.error("Failed to import profile.")
    
    def cmd_help_interactive(self):
        """Display help information (interactive mode)"""
        print("\nAvailable Commands:")
        print("  list                     List all available profiles")
        print("  create <name> [desc]     Create a new profile")
        print("  clone <src> <name>       Clone an existing profile")
        print("  edit <profile_id>        Edit an existing profile")
        print("  delete <profile_id>      Delete a profile")
        print("  activate <profile_id>    Activate a profile")
        print("  export <id> <path>       Export a profile to a file")
        print("  import <path> [name]     Import a profile from a file")
        print("  help                     Show this help message")
        print("  exit                     Exit the program")
        
    # Command functions for argparse mode
    def cmd_list(self, args):
        """List available profiles (argparse mode)"""
        self.cmd_list_interactive()
    
    def cmd_create(self, args):
        """Create a new profile (argparse mode)"""
        profile_id = self.profile_manager.create_new_profile(
            name=args.name, 
            description=args.description or "", 
            as_user_profile=args.personal
        )
        
        if profile_id:
            logger.info(f"Profile created successfully: {profile_id}")
        else:
            logger.error("Failed to create profile.")
    
    def cmd_clone(self, args):
        """Clone an existing profile (argparse mode)"""
        profile_id = self.profile_manager.clone_profile(
            profile_id=args.source, 
            new_name=args.name, 
            as_user_profile=args.personal
        )
        
        if profile_id:
            logger.info(f"Profile cloned successfully: {profile_id}")
        else:
            logger.error("Failed to clone profile.")
    
    def cmd_activate(self, args):
        """Activate a profile (argparse mode)"""
        if self.profile_manager.load_profile(args.profile_id):
            self.active_profile_id = args.profile_id
            logger.info(f"Profile activated successfully: {args.profile_id}")
        else:
            logger.error("Failed to activate profile.")
    
    def cmd_delete(self, args):
        """Delete a profile (argparse mode)"""
        # Confirm deletion if not forced
        if not args.force:
            profile_info = self.profile_manager.get_profile_info(args.profile_id)
            if profile_info:
                confirm = input(f"Are you sure you want to delete the profile '{profile_info['name']}'? (y/n): ")
                if confirm.lower() != "y":
                    logger.info("Deletion cancelled.")
                    return
        
        if self.profile_manager.delete_profile(args.profile_id):
            logger.info(f"Profile deleted successfully: {args.profile_id}")
        else:
            logger.error("Failed to delete profile.")
    
    def cmd_export(self, args):
        """Export a profile to a file (argparse mode)"""
        if self.profile_manager.export_profile(args.profile_id, args.output_path):
            logger.info(f"Profile exported successfully to {args.output_path}")
        else:
            logger.error("Failed to export profile.")
    
    def cmd_import(self, args):
        """Import a profile from a file (argparse mode)"""
        profile_id = self.profile_manager.import_profile(
            import_path=args.input_path, 
            new_name=args.name, 
            as_user_profile=args.personal
        )
        
        if profile_id:
            logger.info(f"Profile imported successfully: {profile_id}")
        else:
            logger.error("Failed to import profile.")
    
    def cmd_help(self, args):
        """Display help information (argparse mode)"""
        self.cmd_help_interactive()

def main():
    """Main entry point for the CLI"""
    cli = ProfileManagerCLI()
    
    if len(sys.argv) > 1:
        # Run in command-line mode
        cli.run_command(sys.argv[1:])
    else:
        # Run in interactive mode
        cli.run_interactive()

if __name__ == "__main__":
    main()
