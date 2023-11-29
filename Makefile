.PHONY: default server contracts

default: test

test: 
	poetry run pytest -s tests/*

server: 
	poetry run bionet server

contracts:
	cp ./contracts/out/ServiceRegistry.sol/ServiceRegistry.json ./example/contracts/ServiceRegistry.json
	cp ./contracts/out/IServiceRegistry.sol/IServiceRegistry.json ./example/contracts/IServiceRegistry.json