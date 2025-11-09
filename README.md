
<img width="1822" alt="スクリーンショット 2025-11-09 11 57 44" src="https://github.com/user-attachments/assets/ed6572a5-de46-443f-a419-c417a1648942" />

# rpi5powermonitor
Power Monitoring CLI Tool for Raspberry Pi 5+

## Installation
with uv:
```
uv tool install rpi5powermonitor
```

with pip:
```
pip3 install rpi5powermonitor
```

## Usage
### Command
```bash
rpi5pm
```

### When running without sudo authentication
```
[nercone@dgc-rpi5 ~]$ rpi5pm
Raspberry Pi 5 Power Monitor
This tool requires superuser privileges, enter your password if prompted.
[sudo] password for nercone: 
```

**Note:** When rpi5pm is executed within the expiration date of sudo authentication, the authentication prompt will be skipped.
