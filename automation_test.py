import os
import sys
import argparse
import subprocess
import time
import json
import glob
import unittest
import coverage
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure color output for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text: str, color: str) -> str:
    """Add color to terminal output if supported."""
    if sys.stdout.isatty():  # Only use colors when in a real terminal
        return f"{color}{text}{Colors.END}"
    return text

class TestRunner:
    """Manages discovery and execution of all GestureDrive tests."""
    
    def __init__(self):
        self.project_root = self._find_project_root()
        
        self.test_dir = os.path.join(self.project_root+'Downloads/GestureDrive/GestureDrive', 'tests')
        self.test_categories = ['','unit', 'integration', 'system']
        self.cov = None
        self.start_time = None
        self.results = {}
    
    def _find_project_root(self) -> str:
        """Find project root directory (looks for setup.py or pyproject.toml)."""
        cwd = os.getcwd()
        while cwd != os.path.dirname(cwd):  # Stop at filesystem root
            if (os.path.exists(os.path.join(cwd, 'setup.py')) or 
                os.path.exists(os.path.join(cwd, 'pyproject.toml'))):
                return cwd
            cwd = os.path.dirname(cwd)
            
        # Fallback: use current directory if no project root markers found
        return os.getcwd()
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments for test runner configuration."""
        parser = argparse.ArgumentParser(description='Run automated tests for GestureDrive')
        
        # Main options
        parser.add_argument('--category', '-c', choices=['all'] + self.test_categories,
                           default='all', help='Test category to run (default: all)')
        parser.add_argument('--module', '-m', action='append',
                           help='Specific test modules to run (can be used multiple times)')
        
        # Run mode options
        parser.add_argument('--pytest', action='store_true', 
                           help='Use pytest instead of unittest')
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
        parser.add_argument('--failfast', '-f', action='store_true', 
                           help='Stop on first failure')
        
        # Coverage options
        parser.add_argument('--coverage', action='store_true',
                           help='Generate coverage report')
        parser.add_argument('--html-cov', action='store_true',
                           help='Generate HTML coverage report')
        
        # Report options
        parser.add_argument('--report', '-r',
                           help='Path to save JSON report (default: none)')
        parser.add_argument('--output-dir', '-o', 
                           default='test_results',
                           help='Directory for test result outputs')
        
        return parser.parse_args()
    
    def setup_coverage(self) -> None:
        """Initialize code coverage measurement."""
        if self.cov is None:
            self.cov = coverage.Coverage(
                source=['gesture_drive'],
                omit=['*tests*', '*__pycache__*', '*/venv/*', '*/env/*', '*/site-packages/*']
            )
            self.cov.start()
    
    def discover_tests(self, category: str, module_names: Optional[List[str]]) -> List[str]:
        """Discover test modules based on category and specific module names."""
        all_test_modules = []
        
        if category == 'all':
            categories = self.test_categories
        else:
            categories = [category]
        
        for cat in categories:
            cat_dir = os.path.join(self.test_dir, cat)
            if not os.path.isdir(cat_dir):
                print(f"Warning: Test category directory not found: {cat_dir}")
                continue
            
            # Find test files in category directory
            test_files = []
            for root, _, files in os.walk(cat_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(root, file))
            
            # Convert file paths to module paths
            for file_path in test_files:
                rel_path = os.path.relpath(file_path, self.project_root)
                module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
                
                # Filter by module names if specified
                if not module_names or any(name in module_path for name in module_names):
                    all_test_modules.append(module_path)
        
        return sorted(all_test_modules)
    
    def run_with_unittest(self, test_modules: List[str], args: argparse.Namespace) -> bool:
        """Run tests using unittest framework."""
        success = True
        for module_path in test_modules:
            print(f"\n{colorize('Running tests from:', Colors.BLUE)} {module_path}")
            try:
                # Create test loader and load tests from module
                loader = unittest.TestLoader()
                
                # Import the module and extract tests
                __import__(module_path)
                module = sys.modules[module_path]
                
                # Load tests from the module
                suite = loader.loadTestsFromModule(module)
                
                # Create test runner
                runner = unittest.TextTestRunner(
                    verbosity=2 if args.verbose else 1,
                    failfast=args.failfast
                )
                
                # Run the tests
                result = runner.run(suite)
                
                # Store results
                self.results[module_path] = {
                    'total': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                    'success': result.wasSuccessful()
                }
                
                if not result.wasSuccessful():
                    success = False
                    
            except Exception as e:
                print(f"{colorize('Error running tests from module:', Colors.RED)} {module_path}")
                print(f"{colorize('Exception:', Colors.RED)} {str(e)}")
                success = False
                
                # Store error result
                self.results[module_path] = {
                    'total': 0,
                    'failures': 0, 
                    'errors': 1,
                    'skipped': 0,
                    'success': False,
                    'exception': str(e)
                }
        
        return success
    
    def run_with_pytest(self, test_modules: List[str], args: argparse.Namespace) -> bool:
        """Run tests using pytest framework."""
        try:
            import pytest
        except ImportError:
            print(colorize("Error: pytest not installed. Run 'pip install pytest'", Colors.RED))
            return False
        
        # Convert module paths to file paths for pytest
        test_paths = []
        for module_path in test_modules:
            file_path = os.path.join(self.project_root, 
                                   module_path.replace('.', os.path.sep) + '.py')
            test_paths.append(file_path)
        
        # Build pytest arguments
        pytest_args = ['--no-header']
        
        if args.verbose:
            pytest_args.append('-v')
            
        if args.failfast:
            pytest_args.append('-x')
        
        # Run pytest with specified arguments
        return_code = pytest.main(pytest_args + test_paths)
        
        # Pytest return codes: 0 = all passed, 1 = tests failed, 2 = errors, 4 = no tests ran
        return return_code == 0
    
    def run_tests(self, args: argparse.Namespace) -> bool:
        """Main method to run all tests based on command-line arguments."""
        self.start_time = time.time()
        
        # Create output directory if needed
        if args.report or args.html_cov:
            os.makedirs(args.output_dir, exist_ok=True)
        
        # Start coverage if requested
        if args.coverage or args.html_cov:
            self.setup_coverage()
        
        # Discover tests to run
        test_modules = self.discover_tests(args.category, args.module)
        
        if not test_modules:
            print(colorize("No test modules found matching criteria", Colors.YELLOW))
            return False
        
        print(colorize(f"Discovered {len(test_modules)} test modules", Colors.GREEN))
        for module in test_modules:
            print(f"  {module}")
            
        print(colorize("\n=============== Running Tests ===============", Colors.HEADER))
        
        # Choose test runner based on arguments
        if args.pytest:
            success = self.run_with_pytest(test_modules, args)
        else:
            success = self.run_with_unittest(test_modules, args)
        
        # Generate coverage report if requested
        if args.coverage or args.html_cov:
            self.cov.stop()
            print(colorize("\n=============== Coverage Report ===============", Colors.HEADER))
            
            if args.html_cov:
                html_dir = os.path.join(args.output_dir, 'coverage_html')
                self.cov.html_report(directory=html_dir)
                print(f"HTML coverage report saved to: {html_dir}")
            
            if args.coverage:
                self.cov.report()
        
        # Generate test summary
        self.print_summary(success)
        
        # Save report if requested
        if args.report:
            self.save_report(args.report)
            
        return success
    
    def print_summary(self, overall_success: bool) -> None:
        """Print a summary of test results."""
        duration = time.time() - self.start_time
        
        print(colorize("\n=============== Test Summary ===============", Colors.HEADER))
        
        # Calculate totals
        total_tests = sum(result.get('total', 0) for result in self.results.values())
        total_failures = sum(result.get('failures', 0) for result in self.results.values())
        total_errors = sum(result.get('errors', 0) for result in self.results.values())
        total_skipped = sum(result.get('skipped', 0) for result in self.results.values())
        total_passed = total_tests - total_failures - total_errors - total_skipped
        
        # Print summary
        status_color = Colors.GREEN if overall_success else Colors.RED
        status_text = "PASSED" if overall_success else "FAILED"
        
        print(f"Test Run {colorize(status_text, status_color)}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Tests: {total_tests}")
        print(f"  {colorize('Passed:', Colors.GREEN)} {total_passed}")
        
        if total_failures > 0:
            print(f"  {colorize('Failures:', Colors.RED)} {total_failures}")
        if total_errors > 0:
            print(f"  {colorize('Errors:', Colors.RED)} {total_errors}")
        if total_skipped > 0:
            print(f"  {colorize('Skipped:', Colors.YELLOW)} {total_skipped}")
    
    def save_report(self, report_path: str) -> None:
        """Save test results to a JSON report file."""
        report_file = os.path.join(self.project_root, report_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(report_file)), exist_ok=True)
        
        # Generate report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - self.start_time,
            "results": self.results,
            "summary": {
                "total_modules": len(self.results),
                "total_tests": sum(result.get('total', 0) for result in self.results.values()),
                "total_failures": sum(result.get('failures', 0) for result in self.results.values()),
                "total_errors": sum(result.get('errors', 0) for result in self.results.values()),
                "total_skipped": sum(result.get('skipped', 0) for result in self.results.values())
            }
        }
        
        # Write report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\nTest report saved to: {report_file}")


def main():
    """Main entry point for the test runner script."""
    runner = TestRunner()
    args = runner.parse_args()
    
    try:
        success = runner.run_tests(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest run aborted by user")
        sys.exit(130)  # Standard Unix exit code for SIGINT


if __name__ == "__main__":
    main()