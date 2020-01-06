find_package(Threads REQUIRED)
include(ExternalProject)

set(HT_BUILD_STATIC ON)

if ("${LIB_PATH}" STREQUAL "")
  ExternalProject_Add(HawkTracerExt
      GIT_REPOSITORY https://github.com/amzn/hawktracer.git
      GIT_TAG ${LIB_VERSION}
      INSTALL_COMMAND ""
      CMAKE_ARGS "-DBUILD_STATIC_LIB=${HT_BUILD_STATIC}"
  )
else()
  ExternalProject_Add(HawkTracerExt
      DOWNLOAD_COMMAND ""
      SOURCE_DIR ${LIB_PATH}
      INSTALL_COMMAND ""
      CMAKE_ARGS "-DBUILD_STATIC_LIB=${HT_BUILD_STATIC}"
  )
endif()

if(HT_BUILD_STATIC)
  set(HT_LIB_FILE_NAME "${CMAKE_STATIC_LIBRARY_PREFIX}hawktracer${CMAKE_STATIC_LIBRARY_SUFFIX}")
else()
  set(HT_LIB_FILE_NAME "${CMAKE_SHARED_LIBRARY_PREFIX}hawktracer${CMAKE_SHARED_LIBRARY_SUFFIX}")
endif()

ExternalProject_Get_Property(HawkTracerExt source_dir)
ExternalProject_Get_Property(HawkTracerExt binary_dir)

set(HAWKTRACER_INCLUDE_DIRS ${source_dir}/lib/include ${binary_dir}/lib/include/)
file(MAKE_DIRECTORY ${HAWKTRACER_INCLUDE_DIRS})

set(HAWKTRACER_LIBS_DIRS ${binary_dir}/lib)
if(MSVC)
    set(HAWKTRACER_LIBRARY_PATH "${HAWKTRACER_LIBS_DIRS}/$(Configuration)/${HT_LIB_FILE_NAME}")
else()
    set(HAWKTRACER_LIBRARY_PATH "${HAWKTRACER_LIBS_DIRS}/${HT_LIB_FILE_NAME}")
endif()

add_library(hawktracer UNKNOWN IMPORTED)
set_target_properties(hawktracer PROPERTIES
  IMPORTED_LOCATION ${HAWKTRACER_LIBRARY_PATH}
  INTERFACE_INCLUDE_DIRECTORIES "${HAWKTRACER_INCLUDE_DIRS}"
  INTERFACE_LINK_LIBRARIES "${CMAKE_THREAD_LIBS_INIT}")

add_dependencies(hawktracer HawkTracerExt)
