# LLM-OS Deployment Documentation

This directory contains documentation and scripts for deploying LLM-OS in production.

## Files

### Documentation
- **FILE_STRUCTURE.md** - Comprehensive guide on file structure, security model, and deployment architecture
- **SETUP_GUIDE.md** - Step-by-step setup instructions for different deployment modes
- **README.md** - This file

### Scripts
- **INSTALL.sh** - System-wide installation script (requires root)

## Quick Links

### For Development
Read: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Section 1 (Development Mode)

### For Testing
Read: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Section 2 (User Installation)

### For Production Deployment
Read: [FILE_STRUCTURE.md](FILE_STRUCTURE.md) - Full architectural overview
Then: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Section 3 (System Installation)

## Key Concepts

### Directory Separation

LLM-OS maintains strict separation between:

1. **System Installation** (`/opt/llm-os/`)
   - Core LLM-OS code
   - System configuration
   - Read-only for users
   - Root-owned

2. **User Data** (`~/.llm-os/`)
   - User configuration
   - Command history
   - Logs and cache
   - Per-user, private

3. **Working Directory** (user's current directory)
   - Where user commands execute
   - User's files and projects
   - User permissions apply

### Why This Matters

The screenshots you provided show LLM-OS correctly identifying `/home/siddharth/llm-os` as the working directory. This is fine for development, but in production:

- The core system should be in `/opt/llm-os/` (protected)
- User commands should execute from `~/` (user space)
- Each user should have their own `~/.llm-os/` (isolated)

This ensures:
- **Security**: Users can't modify the core system
- **Multi-user**: Multiple users can use LLM-OS without conflicts
- **Stability**: System updates don't affect user data
- **Simplicity**: Users work in their normal directories

## Implementation Status

### ✅ Completed

1. Created `src/llm_os/paths.py` module for path resolution
2. Updated `src/llm_os/cli.py` to:
   - Use user log directory
   - Initialize user directories on startup
   - Log path configuration
3. Updated `src/llm_os/core.py` to:
   - Use user's working directory (not installation directory)
   - Store history in user directory
4. Created production launcher script
5. Created system installation script
6. Documented architecture and deployment

### 🔄 Testing Needed

Before deploying to Ubuntu for evaluation:

1. **Test Development Mode**
   ```bash
   cd ~/llm-os
   ./launch.sh
   # Verify working directory is correct
   ```

2. **Test User Installation**
   ```bash
   pip install --user -e .
   llm-os
   # Verify paths are correct
   ```

3. **Test System Installation**
   ```bash
   # On Ubuntu VM or test system
   sudo ./docs/deployment/INSTALL.sh
   llm-os
   # Verify multi-user isolation
   ```

### 🎯 Next Steps

1. **Immediate**: Test the changes in development mode
   - Verify paths are correct
   - Check that commands execute in user's working directory
   - Confirm logs go to `~/.llm-os/logs/`

2. **Short-term**: Deploy to Ubuntu test system
   - Use system installation method
   - Test with multiple users
   - Verify security boundaries

3. **Medium-term**: Evaluate and iterate
   - Gather feedback on deployment model
   - Adjust security policies if needed
   - Document any issues found

## Security Model

### File Operations

- **User commands**: Execute with user permissions from user's working directory
- **System files**: Read-only for regular users
- **User data**: Private to each user (700 permissions)

### Boundaries

```
/opt/llm-os/          (root:root, 755)  - System can read, users cannot modify
~/.llm-os/            (user:user, 700)  - User private data
~/                    (user:user, 755)  - User working directory
```

### Isolation

- Each user has independent configuration
- Each user has separate history
- Each user has isolated logs
- No cross-user data access

## Ubuntu Integration

For testing on Ubuntu:

1. **Setup Virtual Machine** (optional but recommended)
   ```bash
   # Create Ubuntu VM
   # Install dependencies
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

2. **Clone Repository**
   ```bash
   git clone /path/to/llm-os
   cd llm-os
   ```

3. **Install System-Wide**
   ```bash
   sudo ./docs/deployment/INSTALL.sh
   ```

4. **Create Test Users**
   ```bash
   sudo useradd -m testuser1
   sudo useradd -m testuser2
   ```

5. **Test Multi-User**
   ```bash
   su - testuser1
   llm-os
   # Test operations
   exit

   su - testuser2
   llm-os
   # Test operations
   # Verify isolation from testuser1
   ```

## Troubleshooting

See [SETUP_GUIDE.md](SETUP_GUIDE.md) - Troubleshooting section

## Contributing

When making changes that affect deployment:

1. Update the documentation in this directory
2. Test all three deployment modes
3. Verify security boundaries are maintained
4. Update the SETUP_GUIDE.md if needed

## Questions?

If you have questions about deployment:

1. Check [FILE_STRUCTURE.md](FILE_STRUCTURE.md) for architectural details
2. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions
3. Check the Troubleshooting section
4. Review the code in `src/llm_os/paths.py`

---

**Last Updated**: 2026-01-12
**Status**: Ready for testing
