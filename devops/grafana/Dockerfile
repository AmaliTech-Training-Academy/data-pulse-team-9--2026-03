FROM grafana/grafana:latest

USER root

# Install wget for health checks
RUN apk add --no-cache wget

# Copy datasource provisioning
COPY datasources.yml /etc/grafana/provisioning/datasources/

USER grafana

EXPOSE 3000
