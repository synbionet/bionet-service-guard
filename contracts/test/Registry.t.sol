// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/ServiceRegistry.sol";

contract ServiceRegistryTest is Test {
    ServiceRegistry public auth;
    address bob = vm.addr(0x1);
    address alice = vm.addr(0x2);

    function setUp() public {
        // This contract will be the admin
        auth = new ServiceRegistry();
        auth.registerUser(alice);
    }

    function testRegister() public {
        auth.registerUser(bob);

        assertTrue(auth.isValidUser(bob));
        assertTrue(auth.isValidUser(alice));
    }

    function testRemove() public {
        auth.remove(alice);
        assertTrue(!auth.isValidUser(alice));
    }
}
