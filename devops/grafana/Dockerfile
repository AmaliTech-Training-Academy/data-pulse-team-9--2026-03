FROM grafana/grafana:latest

USER root

# Install wget for health checks
RUN apk add --no-cache wget

# Copy all provisioning configuration
COPY provisioning/ /etc/grafana/provisioning/

USER grafana

EXPOSE 3000
