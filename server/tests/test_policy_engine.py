"""
Comprehensive Test Suite for Policy Engine
Tests policy loading, validation, evaluation, and actions
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.services.policy_engine import PolicyEngine


class TestPolicyEngineLoading:
    """Test policy loading functionality"""

    @pytest.fixture
    def temp_policy_dir(self):
        """Create temporary directory for policy files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def valid_policy_dict(self) -> Dict[str, Any]:
        """Valid policy configuration"""
        return {
            "policy": {
                "id": "test-policy-001",
                "name": "Test Credit Card Policy",
                "description": "Detect credit card numbers",
                "enabled": True,
                "priority": 10,
                "severity": "high"
            },
            "rules": [
                {
                    "id": "rule-001",
                    "name": "Credit Card Detection",
                    "conditions": [
                        {
                            "field": "classification.type",
                            "operator": "equals",
                            "value": "credit_card"
                        }
                    ],
                    "actions": [
                        {"type": "alert", "severity": "high"},
                        {"type": "block"}
                    ]
                }
            ]
        }

    def test_load_policies_empty_directory(self, temp_policy_dir):
        """Test loading policies from empty directory"""
        engine = PolicyEngine(policies_directory=str(temp_policy_dir))
        engine.load_policies()
        assert len(engine.policies) == 0

    def test_load_single_policy(self, temp_policy_dir, valid_policy_dict):
        """Test loading a single valid policy"""
        policy_file = temp_policy_dir / "test_policy.yml"
        with open(policy_file, 'w') as f:
            yaml.dump(valid_policy_dict, f)

        engine = PolicyEngine(policies_directory=str(temp_policy_dir))
        engine.load_policies()

        assert len(engine.policies) == 1
        assert engine.policies[0]['policy']['id'] == 'test-policy-001'

    def test_load_multiple_policies(self, temp_policy_dir, valid_policy_dict):
        """Test loading multiple policies with priority sorting"""
        # Create multiple policies with different priorities
        for i in range(3):
            policy = valid_policy_dict.copy()
            policy['policy']['id'] = f'test-policy-{i:03d}'
            policy['policy']['priority'] = (i + 1) * 10

            policy_file = temp_policy_dir / f"policy_{i}.yml"
            with open(policy_file, 'w') as f:
                yaml.dump(policy, f)

        engine = PolicyEngine(policies_directory=str(temp_policy_dir))
        engine.load_policies()

        assert len(engine.policies) == 3
        # Check they're sorted by priority
        assert engine.policies[0]['policy']['priority'] == 10
        assert engine.policies[1]['policy']['priority'] == 20
        assert engine.policies[2]['policy']['priority'] == 30

    def test_load_invalid_yaml(self, temp_policy_dir):
        """Test handling of invalid YAML syntax"""
        policy_file = temp_policy_dir / "invalid.yml"
        with open(policy_file, 'w') as f:
            f.write("invalid: yaml: syntax:\n  - bad indentation")

        engine = PolicyEngine(policies_directory=str(temp_policy_dir))
        engine.load_policies()

        # Should handle error gracefully
        assert len(engine.policies) == 0

    def test_load_policy_both_extensions(self, temp_policy_dir, valid_policy_dict):
        """Test loading .yml and .yaml files"""
        # Create .yml file
        yml_file = temp_policy_dir / "policy1.yml"
        with open(yml_file, 'w') as f:
            policy1 = valid_policy_dict.copy()
            policy1['policy']['id'] = 'policy-yml'
            yaml.dump(policy1, f)

        # Create .yaml file
        yaml_file = temp_policy_dir / "policy2.yaml"
        with open(yaml_file, 'w') as f:
            policy2 = valid_policy_dict.copy()
            policy2['policy']['id'] = 'policy-yaml'
            yaml.dump(policy2, f)

        engine = PolicyEngine(policies_directory=str(temp_policy_dir))
        engine.load_policies()

        assert len(engine.policies) == 2


class TestPolicyValidation:
    """Test policy validation logic"""

    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    def test_validate_minimal_policy(self, engine):
        """Test validation of minimal valid policy"""
        policy = {
            "policy": {
                "id": "test-001",
                "name": "Test Policy",
                "enabled": True
            },
            "rules": [
                {
                    "id": "rule-001",
                    "conditions": [{"field": "event.type", "operator": "equals", "value": "file"}],
                    "actions": [{"type": "alert"}]
                }
            ]
        }
        assert engine._validate_policy(policy) is True

    def test_validate_missing_policy_section(self, engine):
        """Test rejection of policy without 'policy' section"""
        policy = {
            "rules": [{"id": "rule-001", "conditions": [], "actions": []}]
        }
        assert engine._validate_policy(policy) is False

    def test_validate_missing_required_fields(self, engine):
        """Test rejection of policy missing required fields"""
        policy = {
            "policy": {"name": "Test"},  # Missing id
            "rules": []
        }
        assert engine._validate_policy(policy) is False

    def test_validate_empty_rules(self, engine):
        """Test policy with empty rules array"""
        policy = {
            "policy": {"id": "test-001", "name": "Test", "enabled": True},
            "rules": []
        }
        # Empty rules should still be valid
        assert engine._validate_policy(policy) is True

    def test_validate_invalid_rule_structure(self, engine):
        """Test rejection of rule with invalid structure"""
        policy = {
            "policy": {"id": "test-001", "name": "Test", "enabled": True},
            "rules": [
                {"id": "rule-001"}  # Missing conditions and actions
            ]
        }
        assert engine._validate_policy(policy) is False


class TestPolicyEvaluation:
    """Test policy evaluation against events"""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create engine with test policies"""
        engine = PolicyEngine(policies_directory=str(tmp_path))

        # Add test policy
        policy = {
            "policy": {
                "id": "credit-card-policy",
                "name": "Credit Card Detection",
                "enabled": True,
                "priority": 10
            },
            "rules": [
                {
                    "id": "cc-rule-001",
                    "name": "Block Credit Cards",
                    "conditions": [
                        {
                            "field": "classification.type",
                            "operator": "equals",
                            "value": "credit_card"
                        }
                    ],
                    "actions": [
                        {"type": "alert", "severity": "critical"},
                        {"type": "block"}
                    ]
                }
            ]
        }

        policy_file = tmp_path / "cc_policy.yml"
        with open(policy_file, 'w') as f:
            yaml.dump(policy, f)

        engine.load_policies()
        return engine

    @pytest.fixture
    def sample_event(self) -> Dict[str, Any]:
        """Sample event with credit card classification"""
        return {
            "event_id": "evt-001",
            "@timestamp": datetime.utcnow().isoformat(),
            "agent": {
                "id": "agent-001",
                "name": "test-agent",
                "ip": "192.168.1.100"
            },
            "event": {
                "type": "clipboard",
                "severity": "medium"
            },
            "classification": [
                {
                    "type": "credit_card",
                    "label": "Credit Card Number",
                    "confidence": 0.95,
                    "pattern": "pan"
                }
            ]
        }

    async def test_evaluate_matching_event(self, engine, sample_event):
        """Test evaluation of event that matches policy"""
        result = await engine.evaluate_event(sample_event)

        assert "policy_matches" in result
        assert len(result["policy_matches"]) > 0
        assert result["policy_matches"][0]["policy_id"] == "credit-card-policy"

    async def test_evaluate_non_matching_event(self, engine):
        """Test evaluation of event that doesn't match any policy"""
        event = {
            "event_id": "evt-002",
            "@timestamp": datetime.utcnow().isoformat(),
            "event": {"type": "file"},
            "classification": []
        }

        result = await engine.evaluate_event(event)
        assert "policy_matches" in result
        assert len(result.get("policy_matches", [])) == 0

    async def test_evaluate_disabled_policy(self, engine, tmp_path, sample_event):
        """Test that disabled policies are not evaluated"""
        # Add disabled policy
        policy = {
            "policy": {
                "id": "disabled-policy",
                "name": "Disabled Test",
                "enabled": False
            },
            "rules": [
                {
                    "id": "rule-001",
                    "conditions": [{"field": "event.type", "operator": "equals", "value": "clipboard"}],
                    "actions": [{"type": "alert"}]
                }
            ]
        }

        policy_file = tmp_path / "disabled.yml"
        with open(policy_file, 'w') as f:
            yaml.dump(policy, f)

        engine.load_policies()
        result = await engine.evaluate_event(sample_event)

        # Should not match disabled policy
        matched_ids = [m["policy_id"] for m in result.get("policy_matches", [])]
        assert "disabled-policy" not in matched_ids


class TestPolicyConditions:
    """Test different condition operators"""

    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    async def test_condition_equals(self, engine):
        """Test 'equals' operator"""
        rule = {
            "conditions": [{"field": "event.type", "operator": "equals", "value": "file"}]
        }
        event = {"event": {"type": "file"}}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_condition_contains(self, engine):
        """Test 'contains' operator"""
        rule = {
            "conditions": [{"field": "content", "operator": "contains", "value": "password"}]
        }
        event = {"content": "This is my password123"}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_condition_regex(self, engine):
        """Test 'regex' operator"""
        rule = {
            "conditions": [
                {"field": "content", "operator": "regex", "value": r"\d{3}-\d{2}-\d{4}"}
            ]
        }
        event = {"content": "SSN: 123-45-6789"}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_condition_greater_than(self, engine):
        """Test 'greater_than' operator"""
        rule = {
            "conditions": [
                {"field": "classification.confidence", "operator": "greater_than", "value": 0.8}
            ]
        }
        event = {"classification": [{"confidence": 0.95}]}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_condition_in(self, engine):
        """Test 'in' operator"""
        rule = {
            "conditions": [
                {"field": "event.type", "operator": "in", "value": ["file", "clipboard", "usb"]}
            ]
        }
        event = {"event": {"type": "clipboard"}}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_condition_exists(self, engine):
        """Test 'exists' operator"""
        rule = {
            "conditions": [{"field": "classification", "operator": "exists"}]
        }
        event = {"classification": [{"type": "credit_card"}]}
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True

    async def test_multiple_conditions_and(self, engine):
        """Test multiple conditions (AND logic)"""
        rule = {
            "conditions": [
                {"field": "event.type", "operator": "equals", "value": "file"},
                {"field": "file.extension", "operator": "in", "value": [".doc", ".docx", ".pdf"]}
            ]
        }
        event = {
            "event": {"type": "file"},
            "file": {"extension": ".pdf"}
        }
        policy = {"policy": {"id": "test"}}

        result = await engine._evaluate_rule(event, rule, policy)
        assert result is True


class TestPolicyActions:
    """Test policy action execution"""

    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    async def test_action_alert(self, engine):
        """Test alert action"""
        event = {"event_id": "evt-001"}
        rule = {
            "actions": [{"type": "alert", "severity": "high"}]
        }
        policy = {"policy": {"id": "test-policy"}}

        result = await engine._execute_rule_actions(event, rule, policy)

        assert "actions_executed" in result
        assert "alert" in result["actions_executed"]

    async def test_action_block(self, engine):
        """Test block action"""
        event = {"event_id": "evt-001"}
        rule = {
            "actions": [{"type": "block"}]
        }
        policy = {"policy": {"id": "test-policy"}}

        result = await engine._execute_rule_actions(event, rule, policy)

        assert result.get("blocked") is True

    async def test_action_quarantine(self, engine):
        """Test quarantine action"""
        event = {"event_id": "evt-001", "file": {"path": "/tmp/test.doc"}}
        rule = {
            "actions": [{"type": "quarantine", "location": "/quarantine"}]
        }
        policy = {"policy": {"id": "test-policy"}}

        result = await engine._execute_rule_actions(event, rule, policy)

        assert "quarantine" in result.get("actions_executed", {})

    async def test_multiple_actions(self, engine):
        """Test execution of multiple actions"""
        event = {"event_id": "evt-001"}
        rule = {
            "actions": [
                {"type": "alert", "severity": "critical"},
                {"type": "block"},
                {"type": "notify", "channel": "email"}
            ]
        }
        policy = {"policy": {"id": "test-policy"}}

        result = await engine._execute_rule_actions(event, rule, policy)

        actions = result.get("actions_executed", {})
        assert "alert" in actions
        assert "notify" in actions
        assert result.get("blocked") is True


class TestPolicyPerformance:
    """Test policy engine performance"""

    @pytest.fixture
    def engine_with_many_policies(self, tmp_path):
        """Create engine with many policies for performance testing"""
        engine = PolicyEngine(policies_directory=str(tmp_path))

        # Create 50 test policies
        for i in range(50):
            policy = {
                "policy": {
                    "id": f"policy-{i:03d}",
                    "name": f"Test Policy {i}",
                    "enabled": True,
                    "priority": i
                },
                "rules": [
                    {
                        "id": f"rule-{i:03d}",
                        "conditions": [
                            {"field": "event.type", "operator": "equals", "value": f"type-{i}"}
                        ],
                        "actions": [{"type": "alert"}]
                    }
                ]
            }

            policy_file = tmp_path / f"policy_{i:03d}.yml"
            with open(policy_file, 'w') as f:
                yaml.dump(policy, f)

        engine.load_policies()
        return engine

    def test_load_many_policies_performance(self, tmp_path):
        """Test loading many policies is reasonably fast"""
        import time

        # Create 100 policies
        for i in range(100):
            policy = {
                "policy": {"id": f"p-{i}", "name": f"Policy {i}", "enabled": True},
                "rules": [{"id": f"r-{i}", "conditions": [], "actions": []}]
            }
            with open(tmp_path / f"p_{i}.yml", 'w') as f:
                yaml.dump(policy, f)

        engine = PolicyEngine(policies_directory=str(tmp_path))

        start = time.time()
        engine.load_policies()
        duration = time.time() - start

        assert len(engine.policies) == 100
        assert duration < 5.0  # Should load in under 5 seconds

    async def test_evaluate_many_policies_performance(self, engine_with_many_policies):
        """Test evaluation against many policies is reasonably fast"""
        import time

        event = {
            "event_id": "evt-001",
            "@timestamp": datetime.utcnow().isoformat(),
            "event": {"type": "type-25"}  # Will match policy-025
        }

        start = time.time()
        result = await engine_with_many_policies.evaluate_event(event)
        duration = time.time() - start

        assert duration < 0.1  # Should evaluate in under 100ms


class TestPatternCompilation:
    """Test regex pattern compilation and caching"""

    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    def test_compile_regex_patterns(self, engine):
        """Test regex patterns are compiled and cached"""
        policy = {
            "policy": {"id": "test-001"},
            "rules": [
                {
                    "id": "rule-001",
                    "conditions": [
                        {"field": "content", "operator": "regex", "value": r"\d{16}"}
                    ]
                }
            ]
        }

        engine._compile_policy_patterns(policy)

        # Check pattern was compiled
        pattern_key = "test-001:rule-001:0"
        assert pattern_key in engine.compiled_patterns
        assert engine.compiled_patterns[pattern_key].pattern == r"\d{16}"

    def test_pattern_reuse(self, engine):
        """Test compiled patterns are reused"""
        policy = {
            "policy": {"id": "test-001"},
            "rules": [
                {
                    "id": "rule-001",
                    "conditions": [
                        {"field": "content", "operator": "regex", "value": r"\d{16}"}
                    ]
                }
            ]
        }

        engine._compile_policy_patterns(policy)
        pattern_key = "test-001:rule-001:0"
        original_pattern = engine.compiled_patterns[pattern_key]

        # Compile again
        engine._compile_policy_patterns(policy)

        # Should be same object (reused)
        assert engine.compiled_patterns[pattern_key] is original_pattern


# Performance benchmarks
@pytest.mark.benchmark
class TestPolicyEngineBenchmarks:
    """Benchmark tests for policy engine"""

    def test_benchmark_policy_loading(self, benchmark, tmp_path):
        """Benchmark policy loading"""
        # Create 50 policies
        for i in range(50):
            policy = {
                "policy": {"id": f"p-{i}", "name": f"Policy {i}", "enabled": True},
                "rules": [
                    {
                        "id": f"r-{i}",
                        "conditions": [{"field": "type", "operator": "equals", "value": f"t-{i}"}],
                        "actions": [{"type": "alert"}]
                    }
                ]
            }
            with open(tmp_path / f"policy_{i}.yml", 'w') as f:
                yaml.dump(policy, f)

        def load():
            engine = PolicyEngine(policies_directory=str(tmp_path))
            engine.load_policies()
            return engine

        result = benchmark(load)
        assert len(result.policies) == 50

    async def test_benchmark_policy_evaluation(self, benchmark, tmp_path):
        """Benchmark policy evaluation"""
        # Setup engine with policies
        engine = PolicyEngine(policies_directory=str(tmp_path))

        policy = {
            "policy": {"id": "test", "name": "Test", "enabled": True},
            "rules": [
                {
                    "id": "rule-001",
                    "conditions": [
                        {"field": "classification.type", "operator": "equals", "value": "credit_card"}
                    ],
                    "actions": [{"type": "alert"}]
                }
            ]
        }

        with open(tmp_path / "test.yml", 'w') as f:
            yaml.dump(policy, f)

        engine.load_policies()

        event = {
            "event_id": "evt-001",
            "classification": [{"type": "credit_card", "confidence": 0.95}]
        }

        result = benchmark(lambda: engine.evaluate_event(event))
