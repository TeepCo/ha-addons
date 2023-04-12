#!/bin/bash

BASE_DIR="/workspaces/ha-addons"

function update_version() {
    PROJECT_DIR="${BASE_DIR}/$1"

    VERSION_LINE=$(grep "##" "${PROJECT_DIR}/CHANGELOG.md" | head -n 1)
    VERSION="${VERSION_LINE:3}"

    sed "s/\(version:\s*\).*$/\1\"${VERSION}\"/" "${PROJECT_DIR}/config.yaml" > "/tmp/version_replace"
    cat "/tmp/version_replace" > "${PROJECT_DIR}/config.yaml"

    sed "s/^\(.*version-v\).*\(-blue.*\)/\1${VERSION}\2/" "${PROJECT_DIR}/README.md" > "/tmp/version_replace"
    cat "/tmp/version_replace" > "${PROJECT_DIR}/README.md"

    sed "s/^\(\[$1-.*version-v\).*\(-blue.*\)/\1${VERSION}\2/" "${BASE_DIR}/README.md" > "/tmp/version_replace"
    cat "/tmp/version_replace" > "${BASE_DIR}/README.md"
}

update_version "cumulus"