# Responsible for: process entrypoint. Loads settings, constructs repos/
# channels/dispatcher, runs exactly one dispatch cycle, and exits with a
# meaningful status code (0 = success, non-zero = failure) so an external
# scheduler (cron/systemd timer/k8s CronJob) can detect and alert on
# failed runs. Contains no business logic of its own — pure wiring + run.