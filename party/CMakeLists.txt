project(party)
cmake_minimum_required(VERSION 3.23)
add_executable(party main.cpp)
# this is heuristically generated, and may not be correct
find_package(jsoncpp CONFIG REQUIRED)

target_link_libraries(party PRIVATE jsoncpp_object jsoncpp_static JsonCpp::JsonCpp)
