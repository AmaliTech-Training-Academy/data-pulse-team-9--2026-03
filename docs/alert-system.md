# Dataset Quality Alert System

## Overview

The **Alert System** is a feature in DataPulse that allows users to monitor the quality of their datasets automatically. It provides real-time email notifications when a dataset's quality score fall below a pre-configured threshold.

## Features

- **Customizable Thresholds**: Each dataset can have its own quality score threshold (0-100).
- **Email Notifications**: Alerts are sent to the user who uploaded the dataset.
- **Suppression Logic**: To avoid spam, only one email is sent when the score drops. Notifications resume only after the score recovers and drops again.

## How to Enable Alerts

1. **Set a Threshold**: Use the API endpoint `POST /api/schedule/alerts/{dataset_id}/` with a JSON body like:
   ```json
   { "threshold": 85 }
   ```
2. **Schedule Checks**: Ensure the dataset has an active schedule (cron expression).
3. **Receive Alerts**: When a scheduled check produces a score below 85, an email will be sent to the owner.

## Email Content

The alert email includes:

- **Dataset Name**
- **Current Quality Score**
- **Defined Threshold**
- **Link to the full report**
