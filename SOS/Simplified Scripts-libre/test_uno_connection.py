"""
Test script to verify UNO/LibreOffice Python connection.
Run this to check if your environment is properly configured.
"""

import sys
import os

def test_uno_import():
    """Test if uno module can be imported."""
    print("=" * 60)
    print("Testing UNO Module Import")
    print("=" * 60)
    
    try:
        import uno
        print("✓ SUCCESS: 'uno' module imported successfully")
        print(f"  Module location: {uno.__file__}")
        return True
    except ImportError as e:
        print("✗ FAILED: Cannot import 'uno' module")
        print(f"  Error: {e}")
        print("\nPossible solutions:")
        print("1. Use LibreOffice's Python interpreter:")
        print('   & "C:\\Program Files\\LibreOffice\\program\\python.exe" test_uno_connection.py')
        print("2. Install uno-python-bridge: pip install uno-python-bridge")
        print("3. Add LibreOffice's program directory to your Python path")
        return False

def test_uno_services():
    """Test if we can create UNO services."""
    print("\n" + "=" * 60)
    print("Testing UNO Service Creation")
    print("=" * 60)
    
    try:
        import uno
        from com.sun.star.beans import PropertyValue
        
        local_context = uno.getComponentContext()
        print("✓ SUCCESS: Got component context")
        
        smgr = local_context.ServiceManager
        print("✓ SUCCESS: Got service manager")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: Cannot create UNO services")
        print(f"  Error: {e}")
        return False

def test_libreoffice_connection():
    """Test if we can connect to LibreOffice."""
    print("\n" + "=" * 60)
    print("Testing LibreOffice Desktop Connection")
    print("=" * 60)
    
    try:
        import uno
        
        local_context = uno.getComponentContext()
        smgr = local_context.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", local_context)
        
        print("✓ SUCCESS: Connected to LibreOffice Desktop service")
        print("  LibreOffice is accessible and ready")
        return True
    except Exception as e:
        print(f"✗ FAILED: Cannot connect to LibreOffice")
        print(f"  Error: {e}")
        print("\nPossible solutions:")
        print("1. Make sure LibreOffice is installed")
        print("2. Try starting LibreOffice manually first")
        print("3. Check if LibreOffice is already running")
        return False

def find_libreoffice_python():
    """Try to locate LibreOffice's Python executable."""
    print("\n" + "=" * 60)
    print("Searching for LibreOffice Python")
    print("=" * 60)
    
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\python.exe",
        r"C:\Program Files (x86)\LibreOffice\program\python.exe",
        r"C:\Program Files\LibreOffice 7\program\python.exe",
        r"C:\Program Files (x86)\LibreOffice 7\program\python.exe",
    ]
    
    found = []
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✓ FOUND: {path}")
            found.append(path)
        else:
            print(f"  Not found: {path}")
    
    if found:
        print(f"\nRecommendation: Use this Python interpreter:")
        print(f'  & "{found[0]}" sdc_simple.py')
    else:
        print("\n✗ Could not locate LibreOffice Python automatically")
        print("  Please locate it manually in your LibreOffice installation")
    
    return found

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "LibreOffice UNO Connection Test" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print()
    
    # Run tests
    uno_import = test_uno_import()
    
    if uno_import:
        uno_services = test_uno_services()
        if uno_services:
            libreoffice_conn = test_libreoffice_connection()
    
    # Try to find LibreOffice Python
    lo_python_paths = find_libreoffice_python()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if uno_import and test_uno_services:
        print("✓ Your environment is properly configured!")
        print("  You can run: python sdc_simple.py")
    elif lo_python_paths:
        print("⚠ Use LibreOffice's Python interpreter:")
        print(f'  & "{lo_python_paths[0]}" sdc_simple.py')
    else:
        print("✗ Setup required. See instructions above.")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
