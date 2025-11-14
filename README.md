
<img width="1822" src="https://github.com/user-attachments/assets/ed6572a5-de46-443f-a419-c417a1648942" />

# rpi5powermonitor
Power Monitoring CLI Tool for Raspberry Pi 5+

## Requiments
- Raspberry Pi 5+
- Linux (recommended: Raspberry Pi OS)
- CPython 3.9+
- `uv` [PyPI↗︎](https://pypi.org/project/uv/) or `pip3` [PyPI↗︎](https://pypi.org/project/pip/)
- `rich` [PyPI↗︎](https://pypi.org/project/rich/)
- `vcgencmd` [Embedded Linux Wiki↗︎](https://elinux.org/RPI_vcgencmd_usage/)

## Installation

### using uv (recommended)
```
uv tool install rpi5powermonitor
```

### using pip3

**System Python:**
```
pip3 install rpi5powermonitor --break-system-packages
```

**Venv Python:**
```
pip3 install rpi5powermonitor
```

## Update

### using uv (recommended)
```
uv tool install rpi5powermonitor --upgrade
```

### using pip3

**System Python:**
```
pip3 install rpi5powermonitor --upgrade --break-system-packages
```

**Venv Python:**
```
pip3 install rpi5powermonitor --upgrade
```

## Usage

### Command
```bash
rpi5pm
```

**When running without sudo authentication**
```
[nercone@dgc-rpi5 ~]$ rpi5pm
Raspberry Pi 5 Power Monitor
This tool requires superuser privileges, enter your password if prompted.
[sudo] password for nercone: 
```

**Note:** When rpi5pm is executed within the expiration date of sudo authentication, the authentication prompt will be skipped.

---

![PyPI - Version](https://img.shields.io/pypi/v/rpi5powermonitor)
