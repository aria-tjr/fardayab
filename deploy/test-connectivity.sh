#!/usr/bin/env bash
set -euo pipefail

# Connectivity Test Script for Hetzner IPv6 Deployment
# This script tests various aspects of the deployment

echo "[+] Testing Hetzner IPv6 deployment connectivity"

# Configuration
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"
PROJECT_DIR="/opt/telegram-bot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test IPv6 connectivity
test_ipv6_connectivity() {
    log_info "Testing IPv6 connectivity"
    
    if ping6 -c 3 $IPV6_ADDRESS >/dev/null 2>&1; then
        log_info "✓ IPv6 ping successful"
    else
        log_error "✗ IPv6 ping failed"
        return 1
    fi
    
    # Test IPv6 gateway
    if ping6 -c 3 fe80::1 >/dev/null 2>&1; then
        log_info "✓ IPv6 gateway reachable"
    else
        log_warn "⚠ IPv6 gateway not reachable"
    fi
}

# Test network interface configuration
test_network_config() {
    log_info "Testing network interface configuration"
    
    # Check if IPv6 address is configured
    if ip -6 addr show | grep -q $IPV6_ADDRESS; then
        log_info "✓ IPv6 address configured: $IPV6_ADDRESS"
    else
        log_error "✗ IPv6 address not configured"
        return 1
    fi
    
    # Check network interface
    INTERFACE=$(ip -6 addr show | grep $IPV6_ADDRESS | head -1 | awk '{print $NF}')
    if [ -n "$INTERFACE" ]; then
        log_info "✓ Network interface: $INTERFACE"
    else
        log_error "✗ Network interface not found"
        return 1
    fi
}

# Test firewall configuration
test_firewall() {
    log_info "Testing firewall configuration"
    
    # Check UFW status
    if ufw status | grep -q "Status: active"; then
        log_info "✓ UFW firewall is active"
    else
        log_warn "⚠ UFW firewall is not active"
    fi
    
    # Check IPv6 iptables rules
    if ip6tables -L | grep -q "ACCEPT.*tcp.*dpt:80"; then
        log_info "✓ HTTP port (80) allowed in IPv6 iptables"
    else
        log_warn "⚠ HTTP port (80) not allowed in IPv6 iptables"
    fi
    
    if ip6tables -L | grep -q "ACCEPT.*tcp.*dpt:443"; then
        log_info "✓ HTTPS port (443) allowed in IPv6 iptables"
    else
        log_warn "⚠ HTTPS port (443) not allowed in IPv6 iptables"
    fi
}

# Test Docker services
test_docker_services() {
    log_info "Testing Docker services"
    
    # Check if Docker is running
    if systemctl is-active --quiet docker; then
        log_info "✓ Docker service is running"
    else
        log_error "✗ Docker service is not running"
        return 1
    fi
    
    # Check if telegram-bot container is running
    if docker ps | grep -q telegram-bot; then
        log_info "✓ Telegram bot container is running"
    else
        log_warn "⚠ Telegram bot container is not running"
    fi
    
    # Check if nginx container is running
    if docker ps | grep -q telegram-bot-nginx; then
        log_info "✓ Nginx container is running"
    else
        log_warn "⚠ Nginx container is not running"
    fi
}

# Test HTTP/HTTPS connectivity
test_http_connectivity() {
    log_info "Testing HTTP/HTTPS connectivity"
    
    # Test HTTP
    if curl -s --connect-timeout 10 --max-time 30 "http://[$IPV6_ADDRESS]" >/dev/null 2>&1; then
        log_info "✓ HTTP connectivity successful"
    else
        log_warn "⚠ HTTP connectivity failed"
    fi
    
    # Test HTTPS (ignore certificate errors for self-signed)
    if curl -s -k --connect-timeout 10 --max-time 30 "https://[$IPV6_ADDRESS]" >/dev/null 2>&1; then
        log_info "✓ HTTPS connectivity successful"
    else
        log_warn "⚠ HTTPS connectivity failed"
    fi
    
    # Test health endpoint
    if curl -s -k --connect-timeout 10 --max-time 30 "https://[$IPV6_ADDRESS]/health" | grep -q "healthy"; then
        log_info "✓ Health endpoint responding"
    else
        log_warn "⚠ Health endpoint not responding"
    fi
}

# Test SSL certificate
test_ssl_certificate() {
    log_info "Testing SSL certificate"
    
    if [ -f "$PROJECT_DIR/ssl/cert.pem" ]; then
        log_info "✓ SSL certificate exists"
        
        # Check certificate validity
        if openssl x509 -in "$PROJECT_DIR/ssl/cert.pem" -text -noout | grep -q "2a01:4f8:1c1a:9cc1::1"; then
            log_info "✓ SSL certificate contains correct IPv6 address"
        else
            log_warn "⚠ SSL certificate does not contain IPv6 address"
        fi
    else
        log_error "✗ SSL certificate not found"
    fi
}

# Test system resources
test_system_resources() {
    log_info "Testing system resources"
    
    # Check disk space
    DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 80 ]; then
        log_info "✓ Disk usage: ${DISK_USAGE}%"
    else
        log_warn "⚠ Disk usage high: ${DISK_USAGE}%"
    fi
    
    # Check memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$MEMORY_USAGE" -lt 80 ]; then
        log_info "✓ Memory usage: ${MEMORY_USAGE}%"
    else
        log_warn "⚠ Memory usage high: ${MEMORY_USAGE}%"
    fi
    
    # Check CPU load
    CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if (( $(echo "$CPU_LOAD < 2.0" | bc -l) )); then
        log_info "✓ CPU load: $CPU_LOAD"
    else
        log_warn "⚠ CPU load high: $CPU_LOAD"
    fi
}

# Test log files
test_log_files() {
    log_info "Testing log files"
    
    # Check if log directory exists
    if [ -d "$PROJECT_DIR/data/logs" ]; then
        log_info "✓ Log directory exists"
    else
        log_warn "⚠ Log directory not found"
    fi
    
    # Check Docker logs
    if docker-compose -f "$PROJECT_DIR/deploy/docker-compose.hetzner.yml" logs --tail=10 >/dev/null 2>&1; then
        log_info "✓ Docker logs accessible"
    else
        log_warn "⚠ Docker logs not accessible"
    fi
}

# Main test function
main() {
    echo "=========================================="
    echo "  HETZNER IPv6 DEPLOYMENT TEST"
    echo "=========================================="
    echo ""
    
    # Run all tests
    test_ipv6_connectivity
    test_network_config
    test_firewall
    test_docker_services
    test_http_connectivity
    test_ssl_certificate
    test_system_resources
    test_log_files
    
    echo ""
    echo "=========================================="
    echo "  TEST COMPLETED"
    echo "=========================================="
    echo ""
    echo "Access URLs:"
    echo "  HTTP:  http://[$IPV6_ADDRESS]"
    echo "  HTTPS: https://[$IPV6_ADDRESS]"
    echo "  Health: https://[$IPV6_ADDRESS]/health"
    echo ""
    echo "For detailed logs:"
    echo "  docker-compose -f $PROJECT_DIR/deploy/docker-compose.hetzner.yml logs -f"
    echo ""
}

# Run main function
main "$@"
