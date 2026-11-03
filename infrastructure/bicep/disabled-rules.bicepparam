using './disabled-rules.bicep'

// No real Azure identifier is committed. The offline compiler supplies only a
// fictional UUID; a future approved deployment must use the existing private pin.
param diagnosticRuleId = readEnvironmentVariable('SENTINELOPS_EXISTING_RULE_UUID')
