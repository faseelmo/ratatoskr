#!/bin/bash

mkdir test_runner_8x8
cd  test_runner_8x8
cp ../../../simulator/sim .
mkdir config
cp ../2D-8x8/config.xml config/
cp ../2D-8x8/network.xml config/
./sim
cd ..

mkdir test_runner_4x4
cd  test_runner_4x4
cp ../../../simulator/sim .
mkdir config
cp ../2D-4x4/config.xml config/
cp ../2D-4x4/network.xml config/
./sim
