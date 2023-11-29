// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.13;

import "./IServiceRegistry.sol";

/// Example contract used by services to manage authorized user via the guard API.
/// In the future this should integrated in with the fair-protocol.
contract ServiceRegistry is IServiceRegistry {
    address public admin;
    mapping(address => bool) internal _users;

    constructor() {
        // creator is admin for now...
        admin = msg.sender;
    }

    /// Register the user as an authorized 'customer'
    function registerUser(address user) public {
        require(msg.sender == admin, "Not the admin");
        require(_users[user] == false, "User already registered");

        _users[user] = true;
        emit Register(address(this), user);
    }

    /// Remove an authorized customer
    function remove(address user) public {
        require(msg.sender == admin, "Not the admin");
        require(_users[user] == true, "User not registered");

        _users[user] = false;
        emit Removed(address(this), user);
    }

    /// Check to see if the given user is authorized to use the service.
    function isValidUser(address user) public view returns (bool) {
        return _users[user];
    }
}
