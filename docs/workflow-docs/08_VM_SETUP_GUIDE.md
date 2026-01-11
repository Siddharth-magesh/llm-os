# LLM-OS: VM Setup Guide

## Overview

This guide covers setting up virtual machines for LLM-OS development and testing. It includes configurations for VMware Workstation Player and VirtualBox, optimized for your hardware (32GB RAM, RTX 3050 4GB).

---

## 1. Choosing a Hypervisor

### 1.1 Comparison

| Feature | VMware Workstation Player | VirtualBox |
|---------|--------------------------|------------|
| **Cost** | Free (personal) | Free (open source) |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **3D Acceleration** | Better | Good |
| **Snapshots** | Limited (Pro only) | Full support (free) |
| **USB Support** | Excellent | Good (with extension pack) |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Linux Guest Support** | Excellent | Excellent |

### 1.2 Recommendation

**For LLM-OS Development**: VirtualBox
- Free snapshot support is valuable for development
- Adequate performance for our needs
- Better for rapid iteration

**For Performance Testing**: VMware Workstation Player
- Better performance for final testing
- More realistic GPU acceleration

---

## 2. VirtualBox Setup

### 2.1 Installation (Windows)

```powershell
# Using winget
winget install Oracle.VirtualBox

# Or download from virtualbox.org
```

### 2.2 Install Extension Pack

1. Download Extension Pack from [virtualbox.org](https://www.virtualbox.org/wiki/Downloads)
2. Double-click to install
3. Accept license agreement

The extension pack adds:
- USB 2.0/3.0 support
- VirtualBox Remote Desktop Protocol
- Disk encryption

### 2.3 Create LLM-OS Development VM

#### VM Configuration

```
Name: LLM-OS-Dev
Type: Linux
Version: Ubuntu (64-bit)
```

#### Hardware Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **RAM** | 16384 MB (16GB) | Half of your 32GB; enough for LLM + apps |
| **CPUs** | 4 | Half of available cores |
| **Video Memory** | 128 MB | Maximum for 3D support |
| **Enable 3D Acceleration** | Yes | Better GUI performance |

#### Storage

```
Controller: SATA
├── LLM-OS-Dev.vdi (80 GB, Dynamic)
└── [Optical] ubuntu-24.04.1-desktop-amd64.iso
```

Create the disk as **dynamically allocated** to save space.

#### Network

```
Adapter 1: NAT (default, for internet access)
Adapter 2: Host-only (optional, for host communication)
```

### 2.4 VM Creation Steps

1. **Click "New"**
2. **Name and OS**:
   - Name: `LLM-OS-Dev`
   - Machine Folder: Default or custom location
   - Type: Linux
   - Version: Ubuntu (64-bit)

3. **Hardware**:
   - Memory: 16384 MB
   - Processors: 4
   - Enable EFI: Yes (recommended for Ubuntu 24.04)

4. **Virtual Hard Disk**:
   - Create a virtual hard disk now
   - VDI (VirtualBox Disk Image)
   - Dynamically allocated
   - Size: 80 GB

5. **Before First Boot** - Adjust settings:
   - Settings → Display → Video Memory: 128 MB
   - Settings → Display → Enable 3D Acceleration: ✓
   - Settings → System → Enable EFI: ✓
   - Settings → Storage → Attach Ubuntu ISO to optical drive

### 2.5 Install Ubuntu in VM

1. Start the VM
2. Select "Try or Install Ubuntu"
3. Choose language, keyboard
4. Select "Install Ubuntu"
5. Installation type: "Erase disk and install Ubuntu"
6. Create user: `llmos` / `llmos` (for dev convenience)
7. Wait for installation to complete
8. Restart

### 2.6 Install Guest Additions

After Ubuntu is installed:

```bash
# Inside the VM
sudo apt update
sudo apt install -y build-essential dkms linux-headers-$(uname -r)

# Insert Guest Additions CD (from VirtualBox menu)
# Devices → Insert Guest Additions CD Image...

# Mount and run
sudo mount /dev/cdrom /mnt
cd /mnt
sudo ./VBoxLinuxAdditions.run

# Reboot
sudo reboot
```

Guest Additions provide:
- Shared folders
- Seamless mouse integration
- Better display resolution
- Shared clipboard

### 2.7 Configure Shared Folders

```bash
# In VirtualBox: Settings → Shared Folders → Add
# Folder Path: C:\Users\YourName\llm-os-project
# Folder Name: llm-os-project
# Auto-mount: Yes
# Mount Point: /home/llmos/shared

# In VM: Add user to vboxsf group
sudo usermod -aG vboxsf llmos
# Log out and back in
```

### 2.8 Create Snapshots

Before major changes, create snapshots:

1. Machine → Take Snapshot
2. Name: "Fresh Ubuntu Install" / "Pre-LLM-OS Install" / etc.

Snapshots allow instant rollback to previous states.

---

## 3. VMware Workstation Player Setup

### 3.1 Installation (Windows)

1. Download from [vmware.com/products/workstation-player](https://www.vmware.com/products/workstation-player.html)
2. Run installer
3. Accept license (free for personal use)
4. Complete installation

### 3.2 Create LLM-OS Development VM

#### Create New VM

1. Click "Create a New Virtual Machine"
2. Installer disc image file (ISO): Select Ubuntu ISO
3. VMware will detect "Ubuntu 64-bit"

#### VM Settings

| Setting | Value |
|---------|-------|
| **Name** | LLM-OS-Dev |
| **Location** | Your choice |
| **Disk Size** | 80 GB |
| **Store as single file** | Yes (better performance) |

#### Customize Hardware

Click "Customize Hardware" before finishing:

| Component | Setting |
|-----------|---------|
| **Memory** | 16384 MB |
| **Processors** | 4 cores |
| **Network** | NAT |
| **Display** | Accelerate 3D graphics: Yes |
| **Display** | Graphics Memory: 1 GB |

### 3.3 Install VMware Tools

After Ubuntu installation:

```bash
# VMware Tools are usually auto-installed via open-vm-tools
sudo apt install -y open-vm-tools open-vm-tools-desktop

# Reboot
sudo reboot
```

### 3.4 Shared Folders (VMware)

1. VM → Settings → Options → Shared Folders
2. Add folder from host
3. Enable "Always enabled"

Access in VM: `/mnt/hgfs/folder-name`

---

## 4. Optimal VM Configuration for LLM-OS

### 4.1 Resource Allocation

Given your system (32GB RAM, RTX 3050):

```
┌─────────────────────────────────────────────────────────┐
│                    Host System (Windows)                 │
│                                                          │
│  RAM: 32 GB total                                       │
│  ├── Windows: ~8 GB                                     │
│  └── VM: 16 GB (available for LLM-OS)                  │
│                                                          │
│  CPU: Allocate 4-6 cores to VM                         │
│                                                          │
│  GPU: Limited passthrough (3D acceleration only)        │
│       Local LLM will use VM's virtual CPU               │
│       (GPU passthrough is complex, not recommended)     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 LLM Considerations

**Important**: GPU passthrough to VMs is complex. For local LLM:

- **Option A**: Run Ollama on Windows host, access from VM via network
- **Option B**: Use CPU-only inference in VM (slower but works)
- **Option C**: Use cloud LLM APIs from VM

#### Option A: Ollama on Host (Recommended)

```bash
# On Windows host
# Install Ollama from ollama.com

# Start Ollama with network access
set OLLAMA_HOST=0.0.0.0:11434
ollama serve

# In VM, configure to use host's Ollama
export OLLAMA_HOST=192.168.x.x:11434  # Your host IP
```

#### Option B: CPU Inference in VM

```bash
# In VM
# Install Ollama normally
curl -fsSL https://ollama.com/install.sh | sh

# Pull a small model (CPU-friendly)
ollama pull llama3.2:1b  # Smallest, fastest
ollama pull phi3:mini     # Good balance
```

### 4.3 Network Configuration for Development

```
┌─────────────────────────────────────────────────────────┐
│                      Network Setup                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  NAT (Default)                                          │
│  └── VM can access internet                             │
│  └── VM gets private IP (10.0.2.x)                      │
│  └── Host cannot directly access VM                     │
│                                                          │
│  Host-Only (Add as second adapter)                      │
│  └── VM and Host can communicate                        │
│  └── VM gets IP like 192.168.56.x                       │
│  └── Useful for accessing Ollama on host                │
│                                                          │
│  Bridged (Alternative to Host-Only)                     │
│  └── VM appears as separate machine on network          │
│  └── Gets real IP from router                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Recommended Setup**:
- Adapter 1: NAT (for internet)
- Adapter 2: Host-Only (for host communication)

---

## 5. Development Workflow

### 5.1 Typical Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   Development Workflow                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Start VM                                            │
│     └── Boot from snapshot "Dev-Ready"                  │
│                                                          │
│  2. Open Shared Folder                                  │
│     └── /home/llmos/shared/llm-os-project              │
│     └── Edit code in VS Code (host or VM)              │
│                                                          │
│  3. Run & Test in VM                                    │
│     └── python3 src/nl_shell/app.py                    │
│     └── Test MCP servers                                │
│     └── Test LLM integration                            │
│                                                          │
│  4. When making major changes                           │
│     └── Take snapshot first!                            │
│                                                          │
│  5. Build ISO                                           │
│     └── In VM with Cubic                                │
│     └── Test ISO with nested VM or QEMU                 │
│                                                          │
│  6. Test ISO on real hardware                           │
│     └── Create bootable USB                             │
│     └── Boot laptop/desktop                             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.2 VS Code Remote Development

You can edit code on the host and run it in the VM:

1. **Install VS Code on Windows host**
2. **Install "Remote - SSH" extension**
3. **Enable SSH in VM**:
   ```bash
   sudo apt install openssh-server
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```
4. **Get VM IP**: `ip addr show`
5. **Connect from VS Code**: Ctrl+Shift+P → "Remote-SSH: Connect to Host"

### 5.3 File Synchronization

**Option A: Shared Folders** (Recommended)
- Real-time sync
- Works with both VirtualBox and VMware

**Option B: Git**
- Push from host, pull in VM
- Better for version control

**Option C: rsync**
```bash
# Sync from host to VM
rsync -avz /path/to/local/project/ user@vm-ip:/path/to/remote/project/
```

---

## 6. Performance Optimization

### 6.1 VirtualBox Optimizations

```bash
# In VM settings (via VBoxManage or GUI)

# Use paravirtualized network adapter (faster)
VBoxManage modifyvm "LLM-OS-Dev" --nictype1 virtio

# Enable nested paging
VBoxManage modifyvm "LLM-OS-Dev" --nestedpaging on

# Increase video memory
VBoxManage modifyvm "LLM-OS-Dev" --vram 256
```

### 6.2 VM Guest Optimizations

```bash
# Inside the VM

# Disable unnecessary services
sudo systemctl disable cups       # Printing
sudo systemctl disable avahi-daemon  # Network discovery

# Use lightweight desktop (optional)
sudo apt install xfce4
# Select XFCE at login

# Reduce swappiness
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 6.3 SSD Optimization

If your host uses SSD:

```bash
# Enable TRIM for virtual disk
# VirtualBox: Automatic with SATA controller
# VMware: Automatic

# In VM, enable fstrim timer
sudo systemctl enable fstrim.timer
```

---

## 7. Testing LLM-OS ISO in VM

### 7.1 Nested Virtualization

Test the ISO without leaving your development VM:

```bash
# Enable nested virtualization (on host)
# VirtualBox:
VBoxManage modifyvm "LLM-OS-Dev" --nested-hw-virt on

# In dev VM, install QEMU
sudo apt install qemu-system-x86

# Test ISO
qemu-system-x86_64 \
    -cdrom llm-os-0.1.0-amd64.iso \
    -m 4G \
    -boot d \
    -enable-kvm
```

### 7.2 Create Dedicated Test VM

Alternatively, create a separate VM for ISO testing:

| Setting | Value |
|---------|-------|
| **Name** | LLM-OS-Test |
| **RAM** | 8 GB |
| **CPUs** | 2 |
| **Disk** | 30 GB |
| **Boot** | From ISO |

---

## 8. Troubleshooting

### 8.1 Common Issues

| Issue | Solution |
|-------|----------|
| VM very slow | Increase RAM, enable hardware virtualization in BIOS |
| No 3D acceleration | Install Guest Additions/VMware Tools |
| Shared folders not visible | Add user to vboxsf group, remount |
| Network not working | Check NAT settings, restart network service |
| Black screen on boot | Disable 3D acceleration temporarily |

### 8.2 Enable Hardware Virtualization

1. Restart computer, enter BIOS (usually F2, F12, or Del)
2. Find "Virtualization" or "VT-x" setting
3. Enable it
4. Save and exit

### 8.3 Check VM Logs

```bash
# VirtualBox logs
# Located in VM folder: Logs/VBox.log

# VMware logs
# Located in VM folder: vmware.log

# Inside VM
journalctl -xe
dmesg | tail -50
```

---

## 9. Backup Strategy

### 9.1 Snapshot Strategy

```
Snapshots:
├── Fresh-Ubuntu-Install
│   └── After Ubuntu installation, before any changes
├── Dev-Environment-Setup
│   └── After installing dev tools, Python, Node, etc.
├── LLM-OS-Base
│   └── After installing LLM-OS components
└── Working-State-YYYY-MM-DD
    └── Regular checkpoints during development
```

### 9.2 Export VM

For full backup:

```bash
# VirtualBox
VBoxManage export "LLM-OS-Dev" -o llm-os-dev-backup.ova

# VMware
# Use "Export to OVF" from File menu
```

---

## 10. Quick Reference

### 10.1 Useful Commands

```bash
# Get VM IP address
ip addr show

# Check available memory
free -h

# Check disk space
df -h

# Monitor resources
htop

# Check if virtualization extensions work
egrep -c '(vmx|svm)' /proc/cpuinfo
# (Should return > 0)
```

### 10.2 VirtualBox CLI Commands

```bash
# List VMs
VBoxManage list vms

# Start VM headless
VBoxManage startvm "LLM-OS-Dev" --type headless

# Take snapshot
VBoxManage snapshot "LLM-OS-Dev" take "snapshot-name"

# Restore snapshot
VBoxManage snapshot "LLM-OS-Dev" restore "snapshot-name"
```

### 10.3 Network Debugging

```bash
# Check connectivity
ping google.com
ping 192.168.56.1  # Host (if using host-only)

# Check open ports
ss -tulpn

# Test Ollama connection (if on host)
curl http://192.168.56.1:11434/api/tags
```

---

## References

- [VirtualBox Manual](https://www.virtualbox.org/manual/)
- [VMware Workstation Player Documentation](https://docs.vmware.com/en/VMware-Workstation-Player/)
- [Ubuntu VM Best Practices](https://ubuntu.com/tutorials/how-to-run-ubuntu-desktop-on-a-virtual-machine-using-virtualbox)

---

*Document Version: 1.0*
*Last Updated: January 2026*
