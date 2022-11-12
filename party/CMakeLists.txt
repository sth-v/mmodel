project(party)
cmake_minimum_required(VERSION 3.23)
add_executable(party main.cpp)
include(opennurbs/CMakeLists.txt)
set(opennurbs_public_DIR ../../mmodel/party/opennurbs)
# this is heuristically generated, and may not be correct
find_package(pybind11 CONFIG REQUIRED)
include_directories(${HOME}/micromamba)
target_link_libraries(party PRIVATE opennurbs_public)
