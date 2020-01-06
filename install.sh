#!/bin/bash

usage()
{
    echo "see source code for details..."
}

converter_version=master
lib_version=master

while [ "$1" != "" ]; do
    case $1 in
        -b | --build-dir )
            shift
            build_dir=$1
            ;;
        -l | --library-version )
            shift
            lib_version=$1
            ;;
        -p | --library-path )
            shift
            lib_path=$(realpath $1)
            ;;
        -c | --converter-version )
            shift
            converter_version=$1
            ;;
        -k | --converter-path )
            shift
            converter_path=$(realpath $1)
            ;;
        -h | --help )
            usage
            exit
            ;;
        * )
            usage
            exit 1
    esac
    shift
done

if [ -z "$build_dir" ];
then
   echo "Build directory must be specified"
   exit 1
fi

rm -rf $build_dir
mkdir -p $build_dir
pushd $build_dir

if [ -z "$converter_path" ];
then
    echo "Using converter version: $converter_version"
    cargo install --git https://github.com/loganek/hawktracer-converter.git --branch master --root . --force
else
    echo "Using converter from path: $converter_path"
    cargo install --path $converter_path --root .
fi

if [ -z "$lib_path" ];
then
    echo "Using library version: $lib_version"
    cmake ../apps/ -DCMAKE_INSTALL_PREFIX=. -DLIB_VERSION=$lib_version
else
    echo "Using library from path: $lib_path"
    cmake ../apps/ -DCMAKE_INSTALL_PREFIX=. -DLIB_PATH=$lib_path
fi
pwd
cmake --build . --target install
popd
