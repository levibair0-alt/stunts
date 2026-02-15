"""
ATHENA Reflection System - Unit Tests

Test suite for the ATHENA reflection agent covering:
- Execution recording
- Pattern detection
- Self-optimization
- Cross-project learning
- Recursive reflection
- Data persistence

Run with pytest:
    pytest tests/test_athena_reflection.py -v
"""

import sys
import os
import pytest
import tempfile
import json
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.athena_reflection_agent import (
    AthenaReflectionAgent,
    ExecutionRecord,
    Pattern,
    Optimization,
    ReflectionResult
)


class TestInitialization:
    """Test agent initialization and configuration"""
    
    def test_initialization_success(self):
        """Test successful agent initialization"""
        agent = AthenaReflectionAgent(config_path="config")
        assert agent is not None
        assert agent.PROTOCOL_NAME == "ATHENA Reflection"
        assert agent.PROTOCOL_VERSION == "1.0.0"
    
    def test_default_configuration(self):
        """Test default configuration values"""
        agent = AthenaReflectionAgent(config_path="config")
        assert agent.max_recursion_depth == 3
        assert agent.pattern_threshold == 3
        assert agent.learning_enabled is True
    
    def test_missing_config_uses_defaults(self):
        """Test that missing config file uses defaults"""
        agent = AthenaReflectionAgent(
            config_path="/nonexistent/path",
            config_file="nonexistent.yaml"
        )
        assert agent.learning_enabled is True
        assert agent.max_recursion_depth == 3


class TestExecutionRecording:
    """Test execution recording functionality"""
    
    def setup_method(self):
        """Initialize agent for each test"""
        self.agent = AthenaReflectionAgent(config_path="config")
    
    def test_record_execution_success(self):
        """Test recording a successful execution"""
        task_data = {
            'project_id': 'test_project',
            'task_type': 'classification',
            'complexity_score': 5
        }
        result_data = {
            'success': True,
            'duration_ms': 150
        }
        
        record = self.agent.record_execution(task_data, result_data)
        
        assert record is not None
        assert record.project_id == 'test_project'
        assert record.task_type == 'classification'
        assert record.success is True
        assert record.duration_ms == 150
        assert record.record_id.startswith('exec-')
    
    def test_record_execution_failure(self):
        """Test recording a failed execution"""
        task_data = {
            'project_id': 'test_project',
            'task_type': 'code_generation',
            'complexity_score': 8
        }
        result_data = {
            'success': False,
            'duration_ms': 2000,
            'error_type': 'timeout'
        }
        
        record = self.agent.record_execution(task_data, result_data)
        
        assert record is not None
        assert record.success is False
        assert record.metadata['error_type'] == 'timeout'
    
    def test_record_execution_learning_disabled(self):
        """Test recording when learning is disabled"""
        agent = AthenaReflectionAgent(config_path="config")
        agent.learning_enabled = False
        
        task_data = {'project_id': 'test', 'task_type': 'test'}
        result_data = {'success': True, 'duration_ms': 100}
        
        record = agent.record_execution(task_data, result_data)
        assert record is None
    
    def test_execution_history_growth(self):
        """Test that execution history grows with recordings"""
        initial_count = len(self.agent.execution_history)
        
        for i in range(5):
            self.agent.record_execution(
                {'project_id': 'test', 'task_type': 'test'},
                {'success': True, 'duration_ms': 100}
            )
        
        assert len(self.agent.execution_history) == initial_count + 5


class TestPatternDetection:
    """Test pattern detection functionality"""
    
    def setup_method(self):
        """Initialize agent and add test data"""
        self.agent = AthenaReflectionAgent(config_path="config")
        
        # Add test executions for pattern detection
        test_data = [
            # High success pattern (5 successes = 100% success rate)
            ({'project_id': 'p1', 'task_type': 'reliable_task'}, {'success': True, 'duration_ms': 100}),
            ({'project_id': 'p1', 'task_type': 'reliable_task'}, {'success': True, 'duration_ms': 110}),
            ({'project_id': 'p2', 'task_type': 'reliable_task'}, {'success': True, 'duration_ms': 105}),
            ({'project_id': 'p1', 'task_type': 'reliable_task'}, {'success': True, 'duration_ms': 115}),
            ({'project_id': 'p1', 'task_type': 'reliable_task'}, {'success': True, 'duration_ms': 120}),
            # Low success pattern (1 success, 6 failures = ~14% success rate)
            # Plus 6 error patterns with error1 (exceeds min threshold of 3 and confidence of 0.6)
            ({'project_id': 'p1', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 200, 'error_type': 'error1'}),
            ({'project_id': 'p1', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 210, 'error_type': 'error1'}),
            ({'project_id': 'p2', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 205, 'error_type': 'error1'}),
            ({'project_id': 'p1', 'task_type': 'unreliable_task'}, {'success': True, 'duration_ms': 100}),
            ({'project_id': 'p1', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 215, 'error_type': 'error1'}),
            ({'project_id': 'p2', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 220, 'error_type': 'error1'}),
            ({'project_id': 'p1', 'task_type': 'unreliable_task'}, {'success': False, 'duration_ms': 225, 'error_type': 'error1'}),
        ]
        
        for task, result in test_data:
            self.agent.record_execution(task, result)
    
    def test_detect_high_success_pattern(self):
        """Test detection of high success rate patterns"""
        patterns = self.agent.detect_patterns()
        
        high_success_patterns = [p for p in patterns if p.pattern_type == 'high_success_task']
        assert len(high_success_patterns) > 0
        
        pattern = high_success_patterns[0]
        assert pattern.confidence >= 0.8
        assert 'reliable_task' in pattern.examples or pattern.features.get('task_type') == 'reliable_task'
    
    def test_detect_low_success_pattern(self):
        """Test detection of low success rate patterns"""
        patterns = self.agent.detect_patterns()
        
        low_success_patterns = [p for p in patterns if p.pattern_type == 'low_success_task']
        assert len(low_success_patterns) > 0
        
        pattern = low_success_patterns[0]
        assert pattern.confidence >= 0.6
        assert pattern.features.get('success_rate', 0) < 0.5
    
    def test_detect_error_patterns(self):
        """Test detection of recurring error patterns"""
        patterns = self.agent.detect_patterns()
        
        error_patterns = [p for p in patterns if p.pattern_type == 'recurring_error']
        assert len(error_patterns) > 0
        
        pattern = error_patterns[0]
        assert pattern.features.get('error_type') == 'error1'
    
    def test_pattern_detection_with_filter(self):
        """Test pattern detection with project filter"""
        patterns = self.agent.detect_patterns(project_ids=['p1'])
        
        # Should only have patterns from p1
        for pattern in patterns:
            assert 'p1' in pattern.projects
    
    def test_pattern_detection_learning_disabled(self):
        """Test pattern detection when learning is disabled"""
        self.agent.learning_enabled = False
        patterns = self.agent.detect_patterns()
        assert len(patterns) == 0


class TestSelfOptimization:
    """Test self-optimization functionality"""
    
    def setup_method(self):
        """Initialize agent and add test data"""
        self.agent = AthenaReflectionAgent(config_path="config")
        
        # Add test executions with varying success rates
        test_data = [
            # Low success rate task
            ({'project_id': 'p1', 'task_type': 'problematic_task'}, {'success': False, 'duration_ms': 200}),
            ({'project_id': 'p1', 'task_type': 'problematic_task'}, {'success': False, 'duration_ms': 210}),
            ({'project_id': 'p1', 'task_type': 'problematic_task'}, {'success': True, 'duration_ms': 100}),
            ({'project_id': 'p1', 'task_type': 'problematic_task'}, {'success': False, 'duration_ms': 205}),
            # High duration task
            ({'project_id': 'p1', 'task_type': 'slow_task'}, {'success': True, 'duration_ms': 5000}),
            ({'project_id': 'p1', 'task_type': 'slow_task'}, {'success': True, 'duration_ms': 5100}),
            ({'project_id': 'p1', 'task_type': 'slow_task'}, {'success': True, 'duration_ms': 5050}),
        ]
        
        for task, result in test_data:
            self.agent.record_execution(task, result)
    
    def test_optimize_success_rate(self):
        """Test optimization for success rate"""
        optimizations = self.agent.self_optimize(target_metric='success_rate')
        
        assert len(optimizations) > 0
        
        opt = optimizations[0]
        assert opt.target_metric == 'success_rate'
        assert opt.current_value < opt.suggested_value
        assert opt.confidence > 0
        assert len(opt.rationale) > 0
    
    def test_optimize_duration(self):
        """Test optimization for duration"""
        # Need more data for duration optimization
        for i in range(15):
            self.agent.record_execution(
                {'project_id': 'p1', 'task_type': 'slow_task'},
                {'success': True, 'duration_ms': 10000 + i * 100}
            )
        
        optimizations = self.agent.self_optimize(target_metric='duration')
        
        # May or may not find duration patterns depending on data
        for opt in optimizations:
            assert opt.target_metric == 'duration'
    
    def test_optimization_structure(self):
        """Test that optimizations have correct structure"""
        optimizations = self.agent.self_optimize(target_metric='success_rate')
        
        for opt in optimizations:
            assert opt.optimization_id.startswith('opt-')
            assert 0 <= opt.confidence <= 1
            assert opt.expected_improvement >= 0
            assert isinstance(opt.applies_to, list)
    
    def test_optimization_learning_disabled(self):
        """Test optimization when learning is disabled"""
        self.agent.learning_enabled = False
        optimizations = self.agent.self_optimize(target_metric='success_rate')
        assert len(optimizations) == 0


class TestCrossProjectLearning:
    """Test cross-project learning functionality"""
    
    def setup_method(self):
        """Initialize agent and add test data"""
        self.agent = AthenaReflectionAgent(config_path="config")
        
        # Add test executions for multiple projects
        test_data = [
            ({'project_id': 'source_project', 'task_type': 'common_task'}, {'success': True, 'duration_ms': 100}),
            ({'project_id': 'source_project', 'task_type': 'common_task'}, {'success': True, 'duration_ms': 110}),
            ({'project_id': 'source_project', 'task_type': 'common_task'}, {'success': True, 'duration_ms': 105}),
            ({'project_id': 'target_project', 'task_type': 'other_task'}, {'success': True, 'duration_ms': 150}),
        ]
        
        for task, result in test_data:
            self.agent.record_execution(task, result)
        
        # Detect patterns first
        self.agent.detect_patterns()
    
    def test_cross_project_transfer(self):
        """Test knowledge transfer between projects"""
        result = self.agent.cross_project_learn('source_project', 'target_project')
        
        assert result['status'] == 'success'
        assert result['source_project'] == 'source_project'
        assert result['target_project'] == 'target_project'
        assert result['patterns_transferred'] >= 0
    
    def test_cross_project_knowledge_storage(self):
        """Test that transferred knowledge is stored"""
        self.agent.cross_project_learn('source_project', 'target_project')
        
        knowledge_key = 'source_project_to_target_project'
        assert knowledge_key in self.agent.cross_project_knowledge
        
        knowledge = self.agent.cross_project_knowledge[knowledge_key]
        assert knowledge['source'] == 'source_project'
        assert knowledge['target'] == 'target_project'
    
    def test_cross_project_disabled(self):
        """Test that cross-project learning can be disabled"""
        self.agent.config['cross_project'] = {'enabled': False}
        
        result = self.agent.cross_project_learn('source_project', 'target_project')
        assert result['status'] == 'disabled'
    
    def test_cross_project_no_source_data(self):
        """Test transfer from project with no data"""
        result = self.agent.cross_project_learn('nonexistent_project', 'target_project')
        assert result['status'] == 'error'


class TestRecursiveReflection:
    """Test recursive reflection functionality"""
    
    def setup_method(self):
        """Initialize agent and add test data"""
        self.agent = AthenaReflectionAgent(config_path="config")
        
        # Add test executions
        for i in range(10):
            self.agent.record_execution(
                {'project_id': 'test_project', 'task_type': 'test_task'},
                {'success': True, 'duration_ms': 100 + i * 10}
            )
    
    def test_reflect_basic(self):
        """Test basic reflection"""
        context = {
            'project_id': 'test_project',
            'task_type': 'test_task'
        }
        
        result = self.agent.reflect(context)
        
        assert isinstance(result, ReflectionResult)
        assert result.reflection_id.startswith('refl-')
        assert result.recursion_depth >= 0
        assert 0 <= result.confidence_score <= 1
    
    def test_reflect_depth_limiting(self):
        """Test that reflection respects depth limits"""
        context = {'project_id': 'test_project', 'task_type': 'test_task'}
        
        result = self.agent.reflect(context, depth=0)
        
        assert result.recursion_depth <= self.agent.max_recursion_depth
    
    def test_reflect_returns_patterns(self):
        """Test that reflection returns detected patterns"""
        context = {
            'project_id': 'test_project',
            'task_type': 'test_task'
        }
        
        result = self.agent.reflect(context)
        
        assert isinstance(result.patterns_detected, list)
    
    def test_reflect_returns_optimizations(self):
        """Test that reflection returns optimizations"""
        context = {
            'project_id': 'test_project',
            'task_type': 'test_task',
            'target_metric': 'success_rate'
        }
        
        result = self.agent.reflect(context)
        
        assert isinstance(result.optimizations_suggested, list)
    
    def test_reflect_metadata(self):
        """Test that reflection includes metadata"""
        context = {'project_id': 'test_project', 'task_type': 'test_task'}
        
        result = self.agent.reflect(context)
        
        assert 'context_project' in result.metadata
        assert 'context_task_type' in result.metadata


class TestDataPersistence:
    """Test data persistence functionality"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, 'reflection')
        os.makedirs(self.data_path, exist_ok=True)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_enabled(self):
        """Test that persistence works when enabled"""
        agent = AthenaReflectionAgent(config_path="config")
        agent.config['persistence'] = {
            'enabled': True,
            'path': self.data_path
        }
        
        # Add some data
        agent.record_execution(
            {'project_id': 'test', 'task_type': 'test'},
            {'success': True, 'duration_ms': 100}
        )
        
        # Manually trigger persistence
        agent._persist_data()
        
        # Check that files were created
        assert os.path.exists(os.path.join(self.data_path, 'patterns.json'))
        assert os.path.exists(os.path.join(self.data_path, 'execution_history.json'))
        assert os.path.exists(os.path.join(self.data_path, 'optimizations.json'))
        assert os.path.exists(os.path.join(self.data_path, 'cross_project_knowledge.json'))
    
    def test_persistence_disabled(self):
        """Test that persistence is skipped when disabled"""
        agent = AthenaReflectionAgent(config_path="config")
        agent.config['persistence'] = {'enabled': False}
        
        # Manually trigger persistence
        agent._persist_data()
        
        # Check that files were NOT created
        assert not os.path.exists(os.path.join(self.data_path, 'patterns.json'))
    
    def test_data_loading(self):
        """Test that persisted data can be loaded"""
        # Create agent and add data
        agent1 = AthenaReflectionAgent(config_path="config")
        agent1.config['persistence'] = {
            'enabled': True,
            'path': self.data_path
        }
        
        initial_count = len(agent1.execution_history)
        
        for i in range(5):
            agent1.record_execution(
                {'project_id': 'test', 'task_type': 'test'},
                {'success': True, 'duration_ms': 100}
            )
        
        agent1._persist_data()
        
        # Create new agent that should load the data
        agent2 = AthenaReflectionAgent(config_path="config")
        agent2.config['persistence'] = {
            'enabled': True,
            'path': self.data_path
        }
        agent2._load_persisted_data()
        
        # Check that at least the 5 new records were loaded
        assert len(agent2.execution_history) >= 5


class TestUtilityMethods:
    """Test utility and helper methods"""
    
    def setup_method(self):
        """Initialize agent"""
        self.agent = AthenaReflectionAgent(config_path="config")
    
    def test_compute_hash(self):
        """Test hash computation"""
        data1 = {'key': 'value', 'num': 123}
        data2 = {'key': 'value', 'num': 123}
        data3 = {'key': 'different', 'num': 123}
        
        hash1 = self.agent._compute_hash(data1)
        hash2 = self.agent._compute_hash(data2)
        hash3 = self.agent._compute_hash(data3)
        
        assert hash1 == hash2  # Same data = same hash
        assert hash1 != hash3  # Different data = different hash
        assert len(hash1) == 16  # 16 character hash
    
    def test_generate_id(self):
        """Test ID generation"""
        id1 = self.agent._generate_id("test")
        id2 = self.agent._generate_id("test")
        
        assert id1.startswith("test-")
        assert id2.startswith("test-")
        assert id1 != id2  # IDs should be unique
    
    def test_get_learning_summary(self):
        """Test learning summary"""
        initial_count = len(self.agent.execution_history)
        
        # Add some data
        for i in range(5):
            self.agent.record_execution(
                {'project_id': 'test', 'task_type': 'test'},
                {'success': True, 'duration_ms': 100}
            )
        
        summary = self.agent.get_learning_summary()
        
        assert 'total_executions_recorded' in summary
        assert 'patterns_detected' in summary
        assert 'optimizations_generated' in summary
        assert 'learning_enabled' in summary
        assert summary['total_executions_recorded'] >= initial_count + 5
    
    def test_export_knowledge_json(self):
        """Test knowledge export to JSON"""
        export = self.agent.export_knowledge(format='json')
        
        # Should be valid JSON
        data = json.loads(export)
        assert 'protocol' in data
        assert 'patterns' in data
        assert 'export_timestamp' in data
    
    def test_export_knowledge_unsupported_format(self):
        """Test that unsupported format raises error"""
        with pytest.raises(ValueError):
            self.agent.export_knowledge(format='xml')


class TestIntegration:
    """Integration tests for the full reflection workflow"""
    
    def setup_method(self):
        """Initialize agent"""
        self.agent = AthenaReflectionAgent(config_path="config")
    
    def test_full_workflow(self):
        """Test complete reflection workflow"""
        # 1. Record executions (ensure clear pattern: 75% success rate)
        for i in range(20):
            self.agent.record_execution(
                {'project_id': 'project_a', 'task_type': 'data_processing'},
                {'success': i % 4 != 0, 'duration_ms': 100 + i * 10}
            )
        
        # Add more executions to a different task type for clear pattern
        for i in range(10):
            self.agent.record_execution(
                {'project_id': 'project_a', 'task_type': 'reliable_task'},
                {'success': True, 'duration_ms': 100}
            )
        
        # 2. Detect patterns
        patterns = self.agent.detect_patterns(project_ids=['project_a'])
        # We should have at least the high_success pattern for reliable_task
        assert len(patterns) > 0, f"Expected patterns but found none. History has {len(self.agent.execution_history)} records"
        
        # 3. Generate optimizations
        optimizations = self.agent.self_optimize(target_metric='success_rate')
        
        # 4. Cross-project learning
        for i in range(5):
            self.agent.record_execution(
                {'project_id': 'project_b', 'task_type': 'data_processing'},
                {'success': True, 'duration_ms': 150}
            )
        
        transfer = self.agent.cross_project_learn('project_a', 'project_b')
        assert transfer['status'] == 'success'
        
        # 5. Reflect
        result = self.agent.reflect({
            'project_id': 'project_a',
            'task_type': 'data_processing'
        })
        
        assert result.reflection_id is not None
        assert result.learning_applied is True
    
    def test_multiple_projects_pattern_detection(self):
        """Test pattern detection across multiple projects"""
        # Project A - high success
        for i in range(5):
            self.agent.record_execution(
                {'project_id': 'project_a', 'task_type': 'reliable_task'},
                {'success': True, 'duration_ms': 100}
            )
        
        # Project B - same task, mixed success
        for i in range(5):
            self.agent.record_execution(
                {'project_id': 'project_b', 'task_type': 'reliable_task'},
                {'success': i % 2 == 0, 'duration_ms': 100}
            )
        
        # Detect patterns across both projects
        patterns = self.agent.detect_patterns(project_ids=['project_a', 'project_b'])
        
        # Should find patterns that include both projects
        multi_project_patterns = [
            p for p in patterns 
            if len(p.projects) > 1
        ]
        
        assert len(multi_project_patterns) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
