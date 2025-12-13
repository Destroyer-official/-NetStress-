#!/usr/bin/env python3
"""
TLS Mutual Authentication Example

This example demonstrates how to set up and use TLS mutual authentication
for secure distributed NetStress communication.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.distributed import DistributedController, DistributedAgent
from core.distributed import ControllerConfig, AgentConfig
from core.distributed.certificates import CertificateManager


async def setup_certificates():
    """Set up certificates for controller and agents"""
    print("Setting up TLS certificates...")
    
    cert_dir = ".netstress/certs"
    cert_manager = CertificateManager(cert_dir)
    
    # Generate CA certificate
    print("Generating CA certificate...")
    ca_cert, ca_key = cert_manager.ensure_ca_certificate()
    print(f"CA certificate: {ca_cert}")
    
    # Generate controller certificate
    print("Generating controller certificate...")
    controller_cert, controller_key = cert_manager.ensure_controller_certificate(
        "example-controller", ["localhost", "127.0.0.1"]
    )
    print(f"Controller certificate: {controller_cert}")
    
    # Generate agent certificates
    agent_ids = ["agent-01", "agent-02"]
    for agent_id in agent_ids:
        print(f"Generating certificate for {agent_id}...")
        agent_cert, agent_key = cert_manager.generate_agent_certificate(agent_id)
        print(f"Agent {agent_id} certificate: {agent_cert}")
    
    print("Certificate setup complete!")
    return cert_dir


async def run_controller(cert_dir):
    """Run the controller with TLS mutual authentication"""
    print("\nStarting controller with TLS mutual authentication...")
    
    config = ControllerConfig(
        bind_address="127.0.0.1",
        bind_port=19999,  # Use different port for example
        use_mutual_tls=True,
        cert_dir=cert_dir,
        auto_generate_certs=True,
        heartbeat_interval=2.0,
    )
    
    controller = DistributedController(config)
    
    try:
        await controller.start()
        print("Controller started successfully with TLS mutual authentication")
        
        # Display TLS status
        tls_status = controller.get_tls_status()
        print(f"TLS Status: {tls_status}")
        
        # Wait for agents to connect
        print("Waiting for agents to connect...")
        for i in range(30):  # Wait up to 30 seconds
            agents = controller.get_active_agents()
            if len(agents) >= 2:
                print(f"Connected agents: {[a.agent_id for a in agents]}")
                break
            await asyncio.sleep(1)
        
        # Keep controller running
        print("Controller running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down controller...")
    finally:
        await controller.stop()


async def run_agent(agent_id, cert_dir):
    """Run an agent with TLS mutual authentication"""
    print(f"\nStarting {agent_id} with TLS mutual authentication...")
    
    config = AgentConfig(
        controller_host="127.0.0.1",
        controller_port=19999,
        use_mutual_tls=True,
        cert_dir=cert_dir,
        heartbeat_interval=2.0,
    )
    
    agent = DistributedAgent(config)
    
    # Set up a simple attack callback
    async def attack_callback(attack_config, stats_callback):
        print(f"{agent_id}: Starting attack on {attack_config.target}:{attack_config.port}")
        
        # Simulate attack with stats updates
        for i in range(10):
            stats_callback({
                'packets_sent': i * 1000,
                'bytes_sent': i * 1472 * 1000,
                'pps': 1000,
            })
            await asyncio.sleep(1)
        
        print(f"{agent_id}: Attack completed")
    
    agent.set_attack_callback(attack_callback)
    
    try:
        success = await agent.start()
        if success:
            print(f"{agent_id} connected successfully with TLS mutual authentication")
            
            # Keep agent running
            while True:
                await asyncio.sleep(1)
        else:
            print(f"{agent_id} failed to connect")
            
    except KeyboardInterrupt:
        print(f"\nShutting down {agent_id}...")
    finally:
        await agent.stop()


async def main():
    """Main example function"""
    print("TLS Mutual Authentication Example")
    print("=" * 40)
    
    try:
        # Set up certificates
        cert_dir = await setup_certificates()
        
        # Ask user what to run
        print("\nWhat would you like to run?")
        print("1. Controller only")
        print("2. Agent only")
        print("3. Both controller and agents")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            await run_controller(cert_dir)
        
        elif choice == "2":
            agent_id = input("Enter agent ID (e.g., agent-01): ").strip()
            if not agent_id:
                agent_id = "agent-01"
            await run_agent(agent_id, cert_dir)
        
        elif choice == "3":
            # Run controller and agents concurrently
            tasks = [
                asyncio.create_task(run_controller(cert_dir)),
                asyncio.create_task(run_agent("agent-01", cert_dir)),
                asyncio.create_task(run_agent("agent-02", cert_dir)),
            ]
            
            try:
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                print("\nShutting down all components...")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        
        else:
            print("Invalid choice")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample terminated by user")
    except Exception as e:
        print(f"Example failed: {e}")
        sys.exit(1)