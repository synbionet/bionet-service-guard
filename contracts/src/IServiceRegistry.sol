// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.13;

interface IServiceRegistry {
    /// Emitted when admin registers and authorized user
    event Register(address indexed from, address indexed to);
    /// Emitted when admin removes a user
    event Removed(address indexed from, address indexed to);

    function registerUser(address user) external;

    function remove(address user) external;

    function isValidUser(address user) external view returns (bool);
}
