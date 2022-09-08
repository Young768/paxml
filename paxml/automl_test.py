# coding=utf-8
# Copyright 2022 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for automl."""

from typing import Optional
from absl.testing import absltest
from paxml import automl
from paxml import base_experiment
from paxml import base_task
import pyglove as pg


class MetricTest(absltest.TestCase):
  """Tests for automl.Metric class."""

  def test_custom_type_metrics(self):
    m = automl.Metric.train_steps_per_second()
    self.assertEqual(m.pattern, '^train_steps_per_sec$')
    self.assertEqual(m.metric_type, automl.MetricType.CUSTOM)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)

    m = automl.Metric.eval_steps_per_second()
    self.assertEqual(m.pattern, '^eval_steps_per_sec$')
    self.assertEqual(m.metric_type, automl.MetricType.CUSTOM)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)

    m = automl.Metric.decode_steps_per_second()
    self.assertEqual(m.pattern, '^decode_steps_per_sec$')
    self.assertEqual(m.metric_type, automl.MetricType.CUSTOM)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)

    m = automl.Metric.num_params()
    self.assertEqual(m.pattern, '^num_params$')
    self.assertEqual(m.metric_type, automl.MetricType.CUSTOM)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)

  def test_train(self):
    m = automl.Metric.train('loss')
    self.assertEqual(m.metric_type, automl.MetricType.TRAIN_METRICS)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertEqual(m.metric_name, 'loss')
    self.assertIsNone(m.dataset_name)
    self.assertEqual(m.pattern, '^train/loss$')

  def test_eval_train(self):
    m = automl.Metric.eval_train('log_pplx')
    self.assertEqual(m.metric_type, automl.MetricType.EVAL_TRAIN_METRICS)
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertEqual(m.metric_name, 'log_pplx')
    self.assertIsNone(m.dataset_name)
    self.assertEqual(m.pattern, '^eval_train/metrics/log_pplx$')

  def test_eval(self):
    m = automl.Metric.eval('total_loss')
    self.assertEqual(m.metric_type, automl.MetricType.EVAL_METRICS)
    self.assertTrue(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)
    self.assertEqual(m.metric_name, 'total_loss')
    self.assertEqual(m.pattern, '^eval_test_[^/]+/metrics/total_loss$')
    self.assertEqual(
        m.get_value({'eval_test_abc:xyz/metrics/total_loss': 0.1}), 0.1)
    self.assertEqual(
        m.get_values({
            'eval_test_abc:xyz/metrics/total_loss': 0.1,
            'eval_test_xyz:abc/metrics/total_loss': 0.2
        }), [0.1, 0.2])

    m = automl.Metric.eval('total_loss', 'xyz')
    self.assertEqual(m.metric_type, automl.MetricType.EVAL_METRICS)
    self.assertEqual(m.metric_name, 'total_loss')
    self.assertEqual(m.dataset_name, 'xyz')
    self.assertEqual(m.pattern, '^eval_test_xyz/metrics/total_loss$')
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertEqual(
        m.get_values({
            'eval_test_abc/metrics/total_loss': 0.1,
            'eval_test_xyz/metrics/total_loss': 0.2
        }), [0.2])

  def test_eval_scoring(self):
    m = automl.Metric.eval_scoring('blue')
    self.assertEqual(m.metric_type, automl.MetricType.EVAL_SCORING_METRICS)
    self.assertTrue(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)
    self.assertEqual(m.metric_name, 'blue')
    self.assertEqual(m.pattern, '^eval_test_[^/]+/scoring_eval/blue$')
    self.assertEqual(
        m.get_value({'eval_test_abc:xyz/scoring_eval/blue': 0.1}), 0.1)
    self.assertEqual(
        m.get_values({
            'eval_test_abc:xyz/scoring_eval/blue': 0.1,
            'eval_test_xyz:abc/scoring_eval/blue': 0.2
        }), [0.1, 0.2])

    m = automl.Metric.eval_scoring('blue', 'xyz')
    self.assertEqual(m.metric_type, automl.MetricType.EVAL_SCORING_METRICS)
    self.assertEqual(m.metric_name, 'blue')
    self.assertEqual(m.dataset_name, 'xyz')
    self.assertEqual(m.pattern, '^eval_test_xyz/scoring_eval/blue$')
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertEqual(
        m.get_values({
            'eval_test_abc/scoring_eval/blue': 0.1,
            'eval_test_xyz/scoring_eval/blue': 0.2
        }), [0.2])

  def test_decode(self):
    m = automl.Metric.decode('num_decoded')
    self.assertEqual(m.metric_type, automl.MetricType.DECODE_METRICS)
    self.assertTrue(m.applies_to_multiple_datasets)
    self.assertIsNone(m.dataset_name)
    self.assertEqual(m.metric_name, 'num_decoded')
    self.assertEqual(m.pattern, '^decode_test_[^/]+/num_decoded$')
    self.assertEqual(m.get_value({'decode_test_abc:xyz/num_decoded': 1}), 1)
    self.assertEqual(
        m.get_values({
            'decode_test_abc:xyz/num_decoded': 1.,
            'decode_test_xyz:abc/num_decoded': 2.
        }), [1., 2.])

    m = automl.Metric.decode('num_decoded', 'xyz')
    self.assertEqual(m.metric_type, automl.MetricType.DECODE_METRICS)
    self.assertEqual(m.metric_name, 'num_decoded')
    self.assertEqual(m.dataset_name, 'xyz')
    self.assertEqual(m.pattern, '^decode_test_xyz/num_decoded$')
    self.assertFalse(m.applies_to_multiple_datasets)
    self.assertEqual(
        m.get_values({
            'decode_test_abc/num_decoded': 1.,
            'decode_test_xyz/num_decoded': 2.
        }), [2.])

  def test_case_insensitive(self):
    m = automl.Metric.decode('mAP/map')
    self.assertEqual(m.get_value({
        'decode_test_xyz.bcd/mAP/mAP': 1.,
    }), 1.)


class SearchHParamsTest(absltest.TestCase):
  """Tests for search hyperparameters."""

  def test_hyperparameter_tuning(self):
    p = automl.hyperparameter_tuning(automl.Metric.eval('accuracy'))
    # Check algorithm cls for hyperparameter tuning.
    self.assertIs(p.search_algorithm.cls, automl.Sweeping)
    self.assertIs(p.search_reward.cls, automl.SingleObjective)
    self.assertEqual(p.search_reward.metric, automl.Metric.eval('accuracy'))
    self.assertEqual(p.search_reward.goal, 'maximize')
    self.assertEqual(p.max_num_trials, 100)

  def test_neural_architecture_search_single_objective(self):
    p = automl.neural_architecture_search(automl.Metric.eval('accuracy'))
    self.assertIs(p.search_algorithm.cls, automl.RegularizedEvolution)
    self.assertIs(p.search_reward.cls, automl.SingleObjective)
    self.assertEqual(p.search_reward.metric, automl.Metric.eval('accuracy'))
    self.assertEqual(p.max_num_trials, 10000)

  def test_neural_architecture_search_multi_objective(self):
    p = automl.neural_architecture_search([
        automl.Metric.eval('accuracy'),
        automl.Metric.train_steps_per_second()
    ],
                                          150,
                                          max_num_trials=6000)
    self.assertIs(p.search_algorithm.cls, automl.RegularizedEvolution)
    self.assertIs(p.search_reward.cls, automl.MultiObjective)
    self.assertEqual(p.search_reward.metrics, [
        automl.Metric.eval('accuracy'),
        automl.Metric.train_steps_per_second()
    ])
    self.assertEqual(p.search_reward.aggregator.cost_objective, 150)
    self.assertEqual(p.max_num_trials, 6000)

  def test_neural_architecture_search_multi_objective_aggregators(self):
    p = automl.neural_architecture_search([
        automl.Metric.eval('accuracy'),
        automl.Metric.train_steps_per_second()
    ],
                                          150,
                                          reward_type='tunas').search_reward
    self.assertIsInstance(p.aggregator, automl.TunasAbsolute.HParams)
    p = automl.neural_architecture_search([
        automl.Metric.eval('accuracy'),
        automl.Metric.train_steps_per_second()
    ],
                                          150,
                                          reward_type='mnas_hard').search_reward
    self.assertIsInstance(p.aggregator, automl.MnasHard.HParams)
    p = automl.neural_architecture_search([
        automl.Metric.eval('accuracy'),
        automl.Metric.train_steps_per_second()
    ],
                                          150,
                                          reward_type='mnas_soft').search_reward
    self.assertIsInstance(p.aggregator, automl.MnasSoft.HParams)
    with self.assertRaisesRegex(ValueError, 'Unsupported reward type'):
      automl.neural_architecture_search([
          automl.Metric.eval('accuracy'),
          automl.Metric.train_steps_per_second()
      ],
                                        150,
                                        reward_type='unsupported_type')


class SearchAlgorithmsTest(absltest.TestCase):
  """Tests for search algorithms."""

  def test_random_search(self):
    algorithm = automl.RandomSearch.HParams(seed=1).Instantiate()
    self.assertTrue(pg.eq(algorithm(), pg.geno.Random(seed=1)))

  def test_sweeping(self):
    algorithm = automl.Sweeping.HParams().Instantiate()
    self.assertTrue(pg.eq(algorithm(), pg.geno.Sweeping()))

  def test_regularized_evolution(self):
    algorithm = automl.RegularizedEvolution.HParams(
        population_size=10, tournament_size=5).Instantiate()
    self.assertTrue(
        pg.eq(
            algorithm(),
            pg.evolution.regularized_evolution(
                mutator=pg.evolution.mutators.Uniform(),
                population_size=10,
                tournament_size=5)))


class RewardsTest(absltest.TestCase):
  """Tests for common reward functions."""

  def test_single_objective(self):
    reward_fn = automl.SingleObjective.HParams(
        metric=automl.Metric.eval('accuracy')).Instantiate()
    self.assertIsInstance(reward_fn, automl.SingleObjective)
    self.assertEqual(reward_fn({'eval_test_abc/metrics/accuracy': 0.9}, 0), 0.9)

    reward_fn = automl.SingleObjective.HParams(
        metric=automl.Metric.eval('accuracy'), goal='minimize').Instantiate()
    self.assertIsInstance(reward_fn, automl.SingleObjective)
    self.assertEqual(
        reward_fn({'eval_test_abc/metrics/accuracy': 0.9}, 0), -0.9)

    with self.assertRaisesRegex(ValueError,
                                'Param `metric` should not be None'):
      _ = automl.SingleObjective.HParams()

    with self.assertRaisesRegex(ValueError,
                                'Param `goal` should be either .*'):
      _ = automl.SingleObjective.HParams(
          metric=automl.Metric.eval('accuracy'), goal='abc')

    with self.assertRaisesRegex(KeyError,
                                'Metric .* does not match with any metrics'):
      _ = reward_fn({'eval_test_abc/log_pplx': 0.1}, 0)

  def test_multi_objective(self):
    reward_fn = automl.MultiObjective.HParams(
        metrics=[automl.Metric.eval('accuracy')]).Instantiate()
    self.assertIsInstance(reward_fn, automl.MultiObjective)
    self.assertEqual(reward_fn({'eval_test_abc/metrics/accuracy': 0.9}, 0), 0.9)

    reward_fn = automl.MultiObjective.HParams(
        metrics=[
            automl.Metric.eval('accuracy'),
            automl.Metric.train_steps_per_second()
        ],
        aggregator=automl.MnasHard.HParams(cost_objective=150)).Instantiate()
    self.assertIsInstance(reward_fn, automl.MultiObjective)
    self.assertEqual(
        reward_fn(
            {
                'eval_test_abc/metrics/accuracy': 0.9,
                'train_steps_per_sec': 140
            }, 0), 0.9)

    with self.assertRaisesRegex(ValueError,
                                'Param `metrics` must be provided.'):
      _ = automl.MultiObjective.HParams()

    with self.assertRaisesRegex(ValueError,
                                'Param `aggregator` must be provided.'):
      _ = automl.MultiObjective.HParams(metrics=[
          automl.Metric.eval('accuracy'),
          automl.Metric.train_steps_per_second()
      ])

    with self.assertRaisesRegex(KeyError,
                                'Metric .* does not match with any metrics'):
      _ = reward_fn({'cost': 0.1}, 0)


class MultiObjectiveAggregatorTest(absltest.TestCase):
  """Tests for multi-objective aggregators."""

  def test_tunas_abs(self):
    aggregator = automl.TunasAbsolute.HParams(cost_objective=1).Instantiate()
    self.assertEqual(aggregator([2., 2.]), 1.93)

    with self.assertRaisesRegex(ValueError,
                                'Only two objectives are supported'):
      aggregator([2., 2., 2.])

    with self.assertRaisesRegex(ValueError,
                                'Param `cost_objective` must be provided.'):
      _ = automl.TunasAbsolute.HParams()

  def test_mnas_hard(self):
    aggregator = automl.MnasHard.HParams(cost_objective=1).Instantiate()
    self.assertEqual(aggregator([2., 2.]), 1.9052759960878747)

  def test_mnas_soft(self):
    aggregator = automl.MnasSoft.HParams(cost_objective=2.).Instantiate()
    self.assertEqual(aggregator([2., 1.]), 2.0994333672461347)


class EarlyStoppingErrorTest(absltest.TestCase):
  """Tests for early stopping error."""

  def test_skip(self):
    e = automl.EarlyStoppingError(skip_reason='Test stop')
    self.assertTrue(e.skip)
    self.assertEqual(e.skip_reason, 'Test stop')
    self.assertIsNone(e.step)
    self.assertIsNone(e.reward)
    self.assertIsNone(e.metrics)
    self.assertIsNone(e.checkpoint)

  def test_early_stop_without_skip(self):
    # Test stopping with providing final reward.
    e = automl.EarlyStoppingError(skip=False, step=1, reward=1.0)
    self.assertFalse(e.skip)
    self.assertIsNone(e.skip_reason)
    self.assertEqual(e.step, 1)
    self.assertEqual(e.reward, 1.0)
    self.assertIsNone(e.metrics)
    self.assertIsNone(e.checkpoint)

    # Test stopping with providing metrics.
    e = automl.EarlyStoppingError(
        skip=False, step=1, metrics={'accuracy': 1.0}, checkpoint_path='/path')
    self.assertFalse(e.skip)
    self.assertIsNone(e.skip_reason)
    self.assertEqual(e.step, 1)
    self.assertIsNone(e.reward)
    self.assertEqual(e.metrics, {'accuracy': 1.0})
    self.assertEqual(e.checkpoint, '/path')

    with self.assertRaisesRegex(
        ValueError, '`step` must be provided when `skip` is set to False'):
      _ = automl.EarlyStoppingError(skip=False)

    with self.assertRaisesRegex(
        ValueError,
        'At least one of `reward` and `metrics` should be provided'):
      _ = automl.EarlyStoppingError(skip=False, step=1)


class MyTask(base_task.BaseTask):
  """Task for testing purpose."""

  class HParams(base_task.BaseTask.HParams):
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    program_str: Optional[str] = None


class RegularExperiment(base_experiment.BaseExperiment):
  """Regular experiment."""

  LEARNING_RATE = 0.1
  BATCH_SIZE = 8
  PROGRAM_STR = 'foo'

  def task(self):
    return MyTask.HParams(
        learning_rate=self.LEARNING_RATE,
        batch_size=self.BATCH_SIZE,
        program_str=self.PROGRAM_STR)

  def datasets(self):
    return []


@pg.members([
    ('init_value', pg.typing.Str())
])
class VarString(pg.hyper.CustomHyper):

  def custom_decode(self, dna):
    return dna.value

  def first_dna(self):
    return pg.DNA(self.init_value)


class TuningExperiment(RegularExperiment):
  """Tuning experiment."""
  LEARNING_RATE = pg.floatv(0.0, 1.0, name='learning_rate')
  BATCH_SIZE = pg.oneof([8, 16, 32], name='batch_size')
  PROGRAM_STR = VarString(init_value='bar', name='program_str')


class TuningExperimentWithOverride(TuningExperiment):
  """Tuning experiment with modified learning_rate."""
  LEARNING_RATE = 0.1


class TuningExperimentWithoutHyperName(RegularExperiment):
  """Tuning experiment without specifying name for `pg.oneof`."""
  BATCH_SIZE = pg.oneof([8, 16, 32])


class ClassLevelHyperPrimitiveTest(absltest.TestCase):
  """Test class-level hyper primitives on experiment specifications."""

  def test_regular_experiment(self):
    """Test enable_class_level_hyper_primitives on regular experiment class."""
    context = pg.hyper.DynamicEvaluationContext()
    with context.collect():
      _ = RegularExperiment().task()
    self.assertEmpty(context.hyper_dict)

  def test_tuning_experiment(self):
    """Test enable_class_level_hyper_primitives on tuning experiment class."""
    context = pg.hyper.DynamicEvaluationContext()
    with context.collect():
      _ = TuningExperiment().task()
    self.assertEqual(
        context.hyper_dict, {
            'learning_rate': pg.floatv(0.0, 1.0, name='learning_rate'),
            'batch_size': pg.oneof([8, 16, 32], name='batch_size'),
            'program_str': VarString(init_value='bar', name='program_str')
        })

  def test_tuning_experiment_with_override(self):
    """Test enable_class_level_hyper_primitives on experiment with override."""
    context = pg.hyper.DynamicEvaluationContext()
    with context.collect():
      _ = TuningExperimentWithOverride().task()
    self.assertEqual(context.hyper_dict, {
        'batch_size': pg.oneof([8, 16, 32], name='batch_size'),
        'program_str': VarString(init_value='bar', name='program_str')
    })

  def test_tuning_experiment_without_hyper_name(self):
    """Test enable_class_level_hyper_primitives on bad experiment spec."""
    context = pg.hyper.DynamicEvaluationContext()
    with context.collect():
      _ = TuningExperimentWithoutHyperName().task()
    self.assertEqual(
        context.hyper_dict, {
            'BATCH_SIZE': pg.oneof([8, 16, 32], name='BATCH_SIZE')
        })


if __name__ == '__main__':
  absltest.main()
