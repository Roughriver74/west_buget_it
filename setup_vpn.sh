#!/bin/bash
# OpenVPN Setup Script for 1C Access
# This script sets up permanent VPN connection on the server

set -e

SERVER="31.129.107.178"
VPN_CONFIG="client08.ovpn"
VPN_NAME="1c-vpn"

echo "===== OpenVPN Setup for 1C Access ====="
echo ""

# Step 1: Create directory and upload VPN config to server
echo "Step 1: Creating directory and uploading VPN config to server..."
ssh "root@${SERVER}" "mkdir -p /etc/openvpn/client"
scp "$VPN_CONFIG" "root@${SERVER}:/etc/openvpn/client/${VPN_NAME}.conf"

# Step 2: Install OpenVPN and setup systemd service
echo "Step 2: Setting up OpenVPN on server..."
ssh "root@${SERVER}" bash << 'ENDSSH'

# Install OpenVPN
echo "Installing OpenVPN..."
apt-get update
apt-get install -y openvpn

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/openvpn-client@.service << 'EOF'
[Unit]
Description=OpenVPN tunnel for %I
After=network-online.target
Wants=network-online.target
Documentation=man:openvpn(8)
Documentation=https://community.openvpn.net/openvpn/wiki/Openvpn24ManPage
Documentation=https://community.openvpn.net/openvpn/wiki/HOWTO

[Service]
Type=notify
PrivateTmp=true
WorkingDirectory=/etc/openvpn/client
ExecStart=/usr/sbin/openvpn --suppress-timestamps --nobind --config %i.conf
CapabilityBoundingSet=CAP_IPC_LOCK CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW CAP_SETGID CAP_SETUID CAP_SYS_CHROOT CAP_DAC_OVERRIDE CAP_AUDIT_WRITE
LimitNPROC=100
DeviceAllow=/dev/null rw
DeviceAllow=/dev/net/tun rw
ProtectSystem=true
ProtectHome=true
KillMode=process
RestartSec=5s
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Create route-up script to add 1C route
echo "Creating route-up script..."
cat > /etc/openvpn/client/route-up.sh << 'EOF'
#!/bin/bash
# Add route to 1C server through VPN

# Wait for interface to be ready
sleep 2

# Add route to 1C network (adjust if needed)
ip route add 10.10.100.0/24 dev tun0 2>/dev/null || true

# Log the route
echo "$(date): Added route to 1C network via tun0" >> /var/log/openvpn-routes.log
ip route show | grep tun0 >> /var/log/openvpn-routes.log
EOF

chmod +x /etc/openvpn/client/route-up.sh

# Add route-up directive to VPN config
if ! grep -q "route-up /etc/openvpn/client/route-up.sh" /etc/openvpn/client/1c-vpn.conf; then
    echo "" >> /etc/openvpn/client/1c-vpn.conf
    echo "# Add route to 1C on connect" >> /etc/openvpn/client/1c-vpn.conf
    echo "route-up /etc/openvpn/client/route-up.sh" >> /etc/openvpn/client/1c-vpn.conf
    echo "script-security 2" >> /etc/openvpn/client/1c-vpn.conf
fi

# Enable and start service
echo "Enabling and starting VPN service..."
systemctl daemon-reload
systemctl enable openvpn-client@1c-vpn
systemctl restart openvpn-client@1c-vpn

# Wait for connection
echo "Waiting for VPN connection..."
sleep 5

# Check status
echo ""
echo "===== VPN Status ====="
systemctl status openvpn-client@1c-vpn --no-pager || true

echo ""
echo "===== Network Interfaces ====="
ip addr show tun0 2>/dev/null || echo "tun0 interface not found"

echo ""
echo "===== Routes ====="
ip route show | grep tun0 || echo "No VPN routes found"

echo ""
echo "===== Testing 1C Connection ====="
ping -c 3 10.10.100.77 || echo "Cannot ping 1C server"

ENDSSH

echo ""
echo "===== Setup Complete ====="
echo "VPN service: openvpn-client@1c-vpn"
echo "Config: /etc/openvpn/client/1c-vpn.conf"
echo "Logs: journalctl -u openvpn-client@1c-vpn -f"
echo ""
echo "To check status: ssh root@${SERVER} systemctl status openvpn-client@1c-vpn"
echo "To restart: ssh root@${SERVER} systemctl restart openvpn-client@1c-vpn"
