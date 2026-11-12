FROM python@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535 AS python
FROM node@sha256:9707cd4542f400df5078df04f9652a272429112f15202d22b5b8bdd148df494f AS node
FROM ghcr.io/astral-sh/uv@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv
FROM jenkins/jenkins@sha256:74401de6a6f92e1afe1b02d1c8e3d0c33f263bfb5275dd8813f9150355f2367b

USER root

COPY --from=python /usr/local/ /usr/local/
COPY --from=node /usr/local/ /usr/local/
COPY --from=uv /uv /usr/local/bin/uv
COPY plugins.lock /usr/share/jenkins/ref/plugins.txt

RUN python3.11 --version \
    && node --version \
    && npm --version \
    && uv --version \
    && jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt --latest false --view-security-warnings

USER jenkins
