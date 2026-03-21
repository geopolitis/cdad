import unittest

from cdad_tools.design_validation import validate_design_text


class DesignValidationTests(unittest.TestCase):
    def test_scope_out_conflict_is_error(self) -> None:
        findings = validate_design_text(
            """# Design

## Objective
Add social login to auth.

## Scope In
Backend auth.

## Scope Out
Social login.

## Constraints
No dependency changes.

## Risks
Token leakage.

## Verification
Run auth token tests.

## Approval Boundaries
Dependency, schema, contract, and security changes need approval.
"""
        )

        self.assertIn("objective_conflicts_with_scope_out", {finding.code for finding in findings})

    def test_token_risk_without_matching_verification_warns(self) -> None:
        findings = validate_design_text(
            """# Design

## Objective
Add login.

## Scope In
Backend auth.

## Scope Out
Social login.

## Constraints
No dependency changes.

## Risks
Token leakage.

## Verification
Run happy path tests.

## Approval Boundaries
Dependency, schema, contract, and security changes need approval.
"""
        )

        self.assertIn("risk_not_reflected_in_verification", {finding.code for finding in findings})


if __name__ == "__main__":
    unittest.main()
