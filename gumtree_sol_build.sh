#!/bin/bash
git clone git@github.com:JoranHonig/tree-sitter-solidity.git
git clone git@github.com:GumTreeDiff/tree-sitter-parser.git
git clone git@github.com:GumTreeDiff/gumtree.git

# download submodules recursively
git submodule update --init --recursive

# mv SolidityTreeSitterTreeGenerator to gumtree repository
cp gumtree-solidity/SolidityTreeSitterTreeGenerator.java gumtree/gen.treesitter/src/main/java/com/github/gumtreediff/gen/treesitter/

# mv tree-sitter-solidity to gumtree repository
mv tree-sitter-solidity tree-sitter-parser/
cp gumtree-solidity/__init__.py tree-sitter-parser/tree_sitter_parser/

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    MSYS_NT*)   machine=Git;;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}

if [ "${machine}" == "Linux" ];
then 
    # build tree-sitter-parser
    cd tree-sitter-parser && git submodule update --init --recursive && pip3 install -r requirements.txt && echo "PATH=$(pwd):\$PATH" >> ~/.bashrc 
    cd .. 
    # build gumtree
    cd gumtree && ./gradlew build && echo "PATH=$(pwd)/dist/build/install/gumtree/bin:\$PATH" >>  ~/.bashrc 
elif [ "${machine}" == "Mac" ];
then
    # build tree-sitter-parser
    cd tree-sitter-parser  && git submodule update --init --recursive  && pip3 install -r requirements.txt && echo "PATH=$(pwd):\$PATH" >> ~/.zshrc 
    cd .. 
    # build gumtree
    cd gumtree && ./gradlew build && echo "PATH=$(pwd)/dist/build/install/gumtree/bin:\$PATH" >>  ~/.zshrc

    git clone git@github.com:GumTreeDiff/jsparser.git
    cd jsparser && npm install && echo "PATH=$(pwd):\$PATH" >> ~/.zshrc 
fi 