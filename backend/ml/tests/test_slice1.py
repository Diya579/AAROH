import unittest

from backend.ml.config import InferenceConfig
from backend.ml.contract import ProcessingStatus
from backend.ml.inference.service import infer
from backend.ml.policies import EvidenceContext, ThresholdConfidencePolicy


class TestSlice1Config(unittest.TestCase):

    def test_default_config(self):
        config = InferenceConfig()

        self.assertEqual(config.target_horizon_days, 7)
        self.assertEqual(config.min_success_confidence, 0.50)
        self.assertEqual(config.abstain_below_confidence, 0.30)

    def test_invalid_horizon_rejected(self):
        with self.assertRaises(ValueError):
            InferenceConfig(target_horizon_days=0)

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(ValueError):
            InferenceConfig(min_success_confidence=1.5)


class TestSlice1Inference(unittest.TestCase):

    def test_inference_without_estimator_fails_closed(self):
        result = infer({})

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("source", result)

    def test_inference_does_not_require_database(self):
        result = infer({"some_feature": 1})

        self.assertIsInstance(result, dict)


class TestSlice1Policy(unittest.TestCase):

    def make_evidence(self):
        return EvidenceContext(
            observation_count=2,
            missing_feature_count=0,
            text_available=True,
            voice_available=False,
            data_quality_insufficient=False,
        )

    def test_low_confidence_abstains(self):
        policy = ThresholdConfidencePolicy()

        decision = policy.decide(
            distress_confidence=0.20,
            prediction_confidence=0.20,
            evidence=self.make_evidence(),
            config=InferenceConfig(),
        )

        self.assertEqual(decision.status, ProcessingStatus.ABSTAINED)

    def test_good_confidence_does_not_abstain(self):
        policy = ThresholdConfidencePolicy()

        decision = policy.decide(
            distress_confidence=0.80,
            prediction_confidence=0.80,
            evidence=self.make_evidence(),
            config=InferenceConfig(),
        )

        self.assertEqual(decision.status, ProcessingStatus.SUCCESS)


class TestSlice1Contract(unittest.TestCase):

    def test_failed_inference_returns_nested_contract(self):
        result = infer({})

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("source", result)
        self.assertIn("model", result)

        self.assertIsNone(result.get("distress"))
        self.assertIsNone(result.get("prediction"))


if __name__ == "__main__":
    unittest.main()