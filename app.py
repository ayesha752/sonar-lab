name: Build

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarqube:
    name: SonarQube
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Cache SonarQube packages
        uses: actions/cache@v4
        with:
          path: ~/.sonar/cache
          key: ${{ runner.os }}-sonar
          restore-keys: ${{ runner.os }}-sonar

      - name: SonarQube Scan
        uses: SonarSource/sonarqube-scan-action@v3.0.0
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          args: >
            -Dsonar.qualitygate.wait=true

      - name: Notify Slack
        if: always()
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          ACTOR: ${{ github.actor }}
          EVENT: ${{ github.event_name }}
          BRANCH: ${{ github.ref_name }}
          PUSH_SHA: ${{ github.sha }}
          PR_SHA: ${{ github.event.pull_request.head.sha }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          PR_TITLE: ${{ github.event.pull_request.title }}
          COMMIT_MSG: ${{ github.event.head_commit.message }}
          REPO: ${{ github.repository }}
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          ORG="ayesha752"
          KEY="ayesha752_sonar-lab"
          API="https://sonarcloud.io/api"

          if [ "$EVENT" = "pull_request" ]; then
            SCOPE="pullRequest=$PR_NUMBER"
            SHA="$PR_SHA"
            WHAT="PR #$PR_NUMBER:$PR_TITLE"
          else
            SCOPE="branch=$BRANCH"
            SHA="$PUSH_SHA"
            WHAT=$(echo "$COMMIT_MSG" | head -n1)
          fi

          SHORT_SHA="${SHA:0:7}"

          GATE_JSON=$(curl -s -u "$SONAR_TOKEN:" "$API/qualitygates/project_status?projectKey=$KEY&$SCOPE")
          GATE=$(echo "$GATE_JSON" | jq -r '.projectStatus.status // "UNKNOWN"')
          FAILED=$(echo "$GATE_JSON" | jq -r '[.projectStatus.conditions[]? | select(.status=="ERROR") | "• " + .metricKey + " = " + (.actualValue // "n/a")] | join("\n")')

          ISSUES_JSON=$(curl -s -u "$SONAR_TOKEN:" "$API/issues/search?organization=$ORG&projects=$KEY&$SCOPE&resolved=false&ps=10")
          TOTAL=$(echo "$ISSUES_JSON" | jq -r '.total // 0')
          ISSUES=$(echo "$ISSUES_JSON" | jq -r '[.issues[]? | "• [" + .severity + "] " + .message + " (" + (.component | split(":")[-1]) + ", line " + ((.line // 0) | tostring) + ")"] | join("\n")')

          if [ "$GATE" = "OK" ]; then ICON=":white_check_mark:"; else ICON=":x:"; fi
          DASH="https://sonarcloud.io/dashboard?id=$KEY&$SCOPE"

          TEXT="$ICON *SonarQube result for$REPO*"
          TEXT="$TEXT"$'\n'"*Pushed by:* $ACTOR"
          TEXT="$TEXT"$'\n'"*Commit:* \`$SHORT_SHA\` - $WHAT"
          TEXT="$TEXT"$'\n'"*Quality Gate:* $GATE"
          if [ -n "$FAILED" ]; then TEXT="$TEXT"$'\n'"*Failed conditions:*"$'\n'"$FAILED"; fi
          TEXT="$TEXT"$'\n'"*Open issues:* $TOTAL"
          if [ -n "$ISSUES" ]; then TEXT="$TEXT"$'\n'"$ISSUES"; fi
          TEXT="$TEXT"$'\n'"<$DASH\vert{}SonarQube dashboard> \vert{} <$RUN_URL|Pipeline run>"

          jq -n --arg text "$TEXT" '{text: $text}' | curl -s -X POST -H 'Content-type: application/json' --data @- "$SLACK_WEBHOOK_URL"
