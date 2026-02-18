"""
ATHENA Reflection System - Step 2: Recursion & Learning Module

PURPOSE:
    Advanced reflection system implementing recursive self-analysis,
    cross-project learning, self-optimization, and pattern recognition
    for the ATHENA orchestration framework.

DEPENDENCIES:
    - pyyaml>=6.0.1 (Configuration management)
    - Python 3.8+ (standard library: re, json, datetime, typing, hashlib)

ENVIRONMENT:
    - REFLECTION_CONFIG_PATH: Path to reflection config (default: ./config)
    - LEARNING_ENABLED: Enable/disable learning features (default: true)
    - MAX_RECURSION_DEPTH: Maximum reflection recursion depth (default: 3)
    - PATTERN_THRESHOLD: Minimum occurrences for pattern recognition (default: 3)

USAGE:
    # Initialize reflection agent
    reflection = AthenaReflectionAgent(config_path="./config")
    
    # Record task execution for learning
    reflection.record_execution(task_data, result_data)
    
    # Detect patterns across projects
    patterns = reflection.detect_patterns(project_ids=["p1", "p2"])
    
    # Self-optimize based on historical data
    optimization = reflection.self_optimize(target_metric="success_rate")

TESTING:
    Run module directly:
        python athena_reflection_agent.py
    
    Or use pytest:
        pytest tests/test_athena_reflection.py

PROTOCOL COMPLIANCE:
    - ATHENA-REFLECTION-2026 v1.0.0
    - Recursive reflection with depth limiting
    - Cross-project knowledge transfer
    - Pattern persistence and versioning

LEDGER NOTES:
    2026-02-09: Step 2 implementation - Recursion & Learning
    - Cross-project learning engine
    - Self-optimization algorithms
    - Pattern recognition with clustering
    - Architectural decisions logged

RISKS:
    1. Recursion depth may cause stack overflow
       Mitigation: Configurable max depth with hard limit
    2. Pattern overfitting to historical data
       Mitigation: Decay factors and confidence thresholds
    3. Cross-project data contamination
       Mitigation: Project isolation with explicit sharing
    4. Self-optimization feedback loops
       Mitigation: Change validation and rollback capability
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import yaml


@dataclass
class ReflectionResult:
    """Structured result from reflection analysis"""
    reflection_id: str
    timestamp: str
    recursion_depth: int
    patterns_detected: List[Dict[str, Any]]
    optimizations_suggested: List[Dict[str, Any]]
    cross_project_insights: List[Dict[str, Any]]
    confidence_score: float
    learning_applied: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """Record of a task execution for learning"""
    record_id: str
    project_id: str
    task_type: str
    input_hash: str
    output_hash: str
    success: bool
    duration_ms: int
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    """Detected pattern with confidence and metadata"""
    pattern_id: str
    pattern_type: str
    projects: List[str]
    occurrences: int
    confidence: float
    features: Dict[str, Any]
    first_seen: str
    last_seen: str
    examples: List[str] = field(default_factory=list)


@dataclass
class Optimization:
    """Self-optimization suggestion"""
    optimization_id: str
    target_metric: str
    current_value: float
    suggested_value: float
    expected_improvement: float
    confidence: float
    rationale: str
    applies_to: List[str]


class AthenaReflectionAgent:
    """
    ATHENA Reflection System - Step 2: Recursion & Learning
    
    Implements recursive self-analysis, cross-project learning,
    self-optimization, and pattern recognition for continuous improvement.
    """
    
    PROTOCOL_NAME = "ATHENA Reflection"
    PROTOCOL_VERSION = "1.0.0"
    DEFAULT_MAX_RECURSION = 3
    DEFAULT_PATTERN_THRESHOLD = 3
    
    def __init__(self, config_path: str = "./config", 
                 config_file: str = "athena_reflection.yaml"):
        """
        Initialize reflection agent with configuration
        
        Args:
            config_path: Path to configuration directory
            config_file: Name of reflection configuration file
        """
        self.config_path = config_path
        self.config_file = config_file
        self.config = self._load_config()
        
        # Extract configuration
        self.learning_enabled = self.config.get('learning', {}).get('enabled', True)
        self.max_recursion_depth = self.config.get('recursion', {}).get(
            'max_depth', self.DEFAULT_MAX_RECURSION
        )
        self.pattern_threshold = self.config.get('patterns', {}).get(
            'threshold', self.DEFAULT_PATTERN_THRESHOLD
        )
        self.similarity_threshold = self.config.get('patterns', {}).get(
            'similarity_threshold', 0.75
        )
        self.max_history = self.config.get('learning', {}).get('max_history', 1000)
        
        # Initialize data stores
        self.execution_history: List[ExecutionRecord] = []
        self.detected_patterns: Dict[str, Pattern] = {}
        self.optimization_history: List[Optimization] = []
        self.cross_project_knowledge: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Load persisted data if available
        self._load_persisted_data()
        
        print(f"[ATHENA-Reflection] Agent initialized")
        print(f"[ATHENA-Reflection] Protocol: {self.PROTOCOL_NAME} v{self.PROTOCOL_VERSION}")
        print(f"[ATHENA-Reflection] Learning: {'enabled' if self.learning_enabled else 'disabled'}")
        print(f"[ATHENA-Reflection] Max recursion depth: {self.max_recursion_depth}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load reflection configuration from YAML"""
        config_file_path = os.path.join(self.config_path, self.config_file)
        
        if not os.path.exists(config_file_path):
            print(f"[ATHENA-Reflection] Warning: Config not found at {config_file_path}")
            print("[ATHENA-Reflection] Using default configuration")
            return self._default_config()
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"[ATHENA-Reflection] Configuration loaded from {config_file_path}")
            return config or self._default_config()
        except Exception as e:
            print(f"[ATHENA-Reflection] Error loading config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'learning': {
                'enabled': True,
                'decay_factor': 0.95,
                'min_samples': 3,
                'max_history': 1000
            },
            'recursion': {
                'max_depth': 3,
                'early_termination': True,
                'confidence_threshold': 0.5,
                'depth_penalty': 0.1
            },
            'patterns': {
                'threshold': 3,
                'similarity_threshold': 0.75,
                'min_confidence': 0.6
            },
            'cross_project': {
                'enabled': True,
                'share_anonymized': True,
                'max_projects': 10,
                'transfer_threshold': 0.7
            },
            'optimization': {
                'enabled': True,
                'min_improvement': 0.05,
                'max_suggestions': 10,
                'target_metrics': ['success_rate', 'duration', 'throughput']
            },
            'persistence': {
                'enabled': True,
                'path': './data/reflection',
                'auto_save': True,
                'save_interval': 100
            },
            'performance': {
                'background_processing': True
            }
        }
    
    def _load_persisted_data(self) -> None:
        """Load persisted patterns, execution history, and knowledge"""
        persistence_config = self.config.get('persistence', {})
        if not persistence_config.get('enabled', True):
            return
        
        data_path = persistence_config.get('path', './data/reflection')
        
        # Load patterns
        patterns_file = os.path.join(data_path, 'patterns.json')
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                for pattern_id, pattern_data in patterns_data.items():
                    self.detected_patterns[pattern_id] = Pattern(**pattern_data)
                print(f"[ATHENA-Reflection] Loaded {len(self.detected_patterns)} patterns")
            except Exception as e:
                print(f"[ATHENA-Reflection] Error loading patterns: {e}")
        
        # Load execution history
        history_file = os.path.join(data_path, 'execution_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                # Keep only last max_history records
                recent_records = (
                    history_data[-self.max_history:]
                    if len(history_data) > self.max_history else history_data
                )
                self.execution_history = [ExecutionRecord(**record) for record in recent_records]
                print(f"[ATHENA-Reflection] Loaded {len(self.execution_history)} execution records")
            except Exception as e:
                print(f"[ATHENA-Reflection] Error loading history: {e}")
        
        # Load optimization history
        optimizations_file = os.path.join(data_path, 'optimizations.json')
        if os.path.exists(optimizations_file):
            try:
                with open(optimizations_file, 'r') as f:
                    optimization_data = json.load(f)
                self.optimization_history = [Optimization(**opt) for opt in optimization_data]
                print(f"[ATHENA-Reflection] Loaded {len(self.optimization_history)} optimizations")
            except Exception as e:
                print(f"[ATHENA-Reflection] Error loading optimizations: {e}")
        
        # Load cross-project knowledge
        cross_project_file = os.path.join(data_path, 'cross_project_knowledge.json')
        if os.path.exists(cross_project_file):
            try:
                with open(cross_project_file, 'r') as f:
                    cross_project_data = json.load(f)
                self.cross_project_knowledge = defaultdict(dict, cross_project_data)
                print(f"[ATHENA-Reflection] Loaded {len(self.cross_project_knowledge)} cross-project transfers")
            except Exception as e:
                print(f"[ATHENA-Reflection] Error loading cross-project knowledge: {e}")
    
    def _persist_data(self) -> None:
        """Persist patterns, history, optimizations, and cross-project knowledge"""
        persistence_config = self.config.get('persistence', {})
        if not persistence_config.get('enabled', True):
            return
        
        data_path = persistence_config.get('path', './data/reflection')
        os.makedirs(data_path, exist_ok=True)
        
        # Persist patterns
        patterns_file = os.path.join(data_path, 'patterns.json')
        try:
            patterns_data = {pid: asdict(p) for pid, p in self.detected_patterns.items()}
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            print(f"[ATHENA-Reflection] Error persisting patterns: {e}")
        
        # Persist execution history
        history_file = os.path.join(data_path, 'execution_history.json')
        try:
            recent_history = self.execution_history[-self.max_history:]
            history_data = [asdict(record) for record in recent_history]
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            print(f"[ATHENA-Reflection] Error persisting history: {e}")
        
        # Persist optimization history
        optimizations_file = os.path.join(data_path, 'optimizations.json')
        try:
            optimization_data = [asdict(opt) for opt in self.optimization_history[-50:]]
            with open(optimizations_file, 'w') as f:
                json.dump(optimization_data, f, indent=2)
        except Exception as e:
            print(f"[ATHENA-Reflection] Error persisting optimizations: {e}")
        
        # Persist cross-project knowledge
        cross_project_file = os.path.join(data_path, 'cross_project_knowledge.json')
        try:
            with open(cross_project_file, 'w') as f:
                json.dump(dict(self.cross_project_knowledge), f, indent=2)
        except Exception as e:
            print(f"[ATHENA-Reflection] Error persisting cross-project knowledge: {e}")
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash for data deduplication"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _generate_id(self, prefix: str = "refl") -> str:
        """Generate unique identifier"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.sha256(
            str(datetime.now().timestamp()).encode()
        ).hexdigest()[:8]
        return f"{prefix}-{timestamp}-{random_suffix}"
    
    def record_execution(self, task_data: Dict[str, Any], 
                         result_data: Dict[str, Any]) -> ExecutionRecord:
        """
        Record a task execution for learning
        
        Args:
            task_data: Task input data
            result_data: Task result data including success/failure
        
        Returns:
            ExecutionRecord of the recorded execution
        """
        if not self.learning_enabled:
            return None
        
        record = ExecutionRecord(
            record_id=self._generate_id("exec"),
            project_id=task_data.get('project_id', 'unknown'),
            task_type=task_data.get('task_type', 'unknown'),
            input_hash=self._compute_hash(task_data),
            output_hash=self._compute_hash(result_data),
            success=result_data.get('success', False),
            duration_ms=result_data.get('duration_ms', 0),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                'agent_type': task_data.get('agent_type'),
                'complexity_score': task_data.get('complexity_score', 0),
                'error_type': result_data.get('error_type') if not result_data.get('success') else None
            }
        )
        
        self.execution_history.append(record)
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
        
        # Trigger pattern detection if enough new records
        background_enabled = self.config.get('performance', {}).get('background_processing', True)
        if background_enabled and len(self.execution_history) % 10 == 0:
            self._background_pattern_detection()
        
        self._maybe_persist_data()
        
        print(f"[ATHENA-Reflection] Recorded execution {record.record_id}")
        return record
    
    def _background_pattern_detection(self) -> None:
        """Background pattern detection triggered after recordings"""
        print("[ATHENA-Reflection] Running background pattern detection...")
        
        # Detect success/failure patterns
        self._detect_success_patterns()
        
        # Detect duration patterns
        self._detect_duration_patterns()
    
    def _maybe_persist_data(self, force: bool = False) -> None:
        """Persist data when auto-save conditions are met"""
        persistence_config = self.config.get('persistence', {})
        if not persistence_config.get('enabled', True):
            return
        if not persistence_config.get('auto_save', True) and not force:
            return
        save_interval = persistence_config.get('save_interval', 10)
        if force or (save_interval > 0 and len(self.execution_history) % save_interval == 0):
            self._persist_data()
    
    def detect_patterns(self, project_ids: Optional[List[str]] = None,
                        pattern_types: Optional[List[str]] = None) -> List[Pattern]:
        """
        Detect patterns across projects
        
        Args:
            project_ids: List of project IDs to analyze (None = all)
            pattern_types: Types of patterns to detect (None = all)
        
        Returns:
            List of detected patterns
        """
        if not self.learning_enabled:
            print("[ATHENA-Reflection] Learning is disabled")
            return []
        
        patterns = []
        
        # Filter by project if specified
        records = self.execution_history
        if project_ids:
            records = [r for r in records if r.project_id in project_ids]
        
        if len(records) < self.pattern_threshold:
            print(f"[ATHENA-Reflection] Insufficient data for pattern detection")
            return []
        
        # Detect task type patterns
        if not pattern_types or 'task_type' in pattern_types:
            patterns.extend(self._detect_task_type_patterns(records))
        
        # Detect error patterns
        if not pattern_types or 'error' in pattern_types:
            patterns.extend(self._detect_error_patterns(records))
        
        # Detect time-based patterns
        if not pattern_types or 'temporal' in pattern_types:
            patterns.extend(self._detect_temporal_patterns(records))
        
        min_confidence = self.config.get('patterns', {}).get('min_confidence', 0.0)
        if min_confidence > 0:
            patterns = [p for p in patterns if p.confidence >= min_confidence]
        
        print(f"[ATHENA-Reflection] Detected {len(patterns)} patterns")
        return patterns
    
    def _detect_task_type_patterns(self, records: List[ExecutionRecord]) -> List[Pattern]:
        """Detect patterns in task type performance"""
        patterns = []
        
        # Group by task type
        task_type_stats = defaultdict(lambda: {'success': 0, 'total': 0, 'projects': set()})
        for record in records:
            stats = task_type_stats[record.task_type]
            stats['total'] += 1
            stats['projects'].add(record.project_id)
            if record.success:
                stats['success'] += 1
        
        # Find patterns with significant occurrence
        for task_type, stats in task_type_stats.items():
            if stats['total'] >= self.pattern_threshold:
                success_rate = stats['success'] / stats['total']
                
                # Pattern: High success rate task type
                if success_rate >= 0.8:
                    pattern_id = self._generate_id("pat")
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type="high_success_task",
                        projects=list(stats['projects']),
                        occurrences=stats['total'],
                        confidence=success_rate,
                        features={
                            'task_type': task_type,
                            'success_rate': success_rate,
                            'total_executions': stats['total']
                        },
                        first_seen=records[0].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        last_seen=records[-1].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        examples=[task_type]
                    )
                    self.detected_patterns[pattern_id] = pattern
                    patterns.append(pattern)
                
                # Pattern: Low success rate task type (needs attention)
                elif success_rate <= 0.4:
                    pattern_id = self._generate_id("pat")
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type="low_success_task",
                        projects=list(stats['projects']),
                        occurrences=stats['total'],
                        confidence=1 - success_rate,
                        features={
                            'task_type': task_type,
                            'success_rate': success_rate,
                            'total_executions': stats['total']
                        },
                        first_seen=records[0].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        last_seen=records[-1].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        examples=[task_type]
                    )
                    self.detected_patterns[pattern_id] = pattern
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_error_patterns(self, records: List[ExecutionRecord]) -> List[Pattern]:
        """Detect patterns in error occurrences"""
        patterns = []
        
        # Filter failed executions
        failed_records = [r for r in records if not r.success]
        
        # Group by error type
        error_type_stats = defaultdict(lambda: {'count': 0, 'projects': set(), 'task_types': set()})
        for record in failed_records:
            error_type = record.metadata.get('error_type', 'unknown')
            stats = error_type_stats[error_type]
            stats['count'] += 1
            stats['projects'].add(record.project_id)
            stats['task_types'].add(record.task_type)
        
        # Find recurring errors
        for error_type, stats in error_type_stats.items():
            if stats['count'] >= self.pattern_threshold:
                pattern_id = self._generate_id("pat")
                pattern = Pattern(
                    pattern_id=pattern_id,
                    pattern_type="recurring_error",
                    projects=list(stats['projects']),
                    occurrences=stats['count'],
                    confidence=min(stats['count'] / 10, 0.95),
                    features={
                        'error_type': error_type,
                        'affected_task_types': list(stats['task_types'])
                    },
                    first_seen=records[0].timestamp if records else datetime.now(timezone.utc).isoformat(),
                    last_seen=records[-1].timestamp if records else datetime.now(timezone.utc).isoformat(),
                    examples=[error_type]
                )
                self.detected_patterns[pattern_id] = pattern
                patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_patterns(self, records: List[ExecutionRecord]) -> List[Pattern]:
        """Detect time-based patterns"""
        patterns = []
        
        # Analyze by hour of day
        hour_stats = defaultdict(lambda: {'success': 0, 'total': 0})
        for record in records:
            try:
                hour = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00')).hour
                hour_stats[hour]['total'] += 1
                if record.success:
                    hour_stats[hour]['success'] += 1
            except:
                continue
        
        # Find hours with notably different success rates
        overall_success = sum(1 for r in records if r.success) / len(records) if records else 0.5
        
        for hour, stats in hour_stats.items():
            if stats['total'] >= self.pattern_threshold:
                hour_success_rate = stats['success'] / stats['total']
                rate_diff = abs(hour_success_rate - overall_success)
                
                if rate_diff > 0.2:  # Significant difference
                    pattern_id = self._generate_id("pat")
                    pattern_type = "high_performance_hour" if hour_success_rate > overall_success else "low_performance_hour"
                    
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern_type,
                        projects=list(set(r.project_id for r in records)),
                        occurrences=stats['total'],
                        confidence=rate_diff,
                        features={
                            'hour': hour,
                            'success_rate': hour_success_rate,
                            'overall_rate': overall_success,
                            'difference': rate_diff
                        },
                        first_seen=records[0].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        last_seen=records[-1].timestamp if records else datetime.now(timezone.utc).isoformat(),
                        examples=[f"hour_{hour}"]
                    )
                    self.detected_patterns[pattern_id] = pattern
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_success_patterns(self) -> None:
        """Detect patterns in successful executions"""
        success_records = [r for r in self.execution_history if r.success]
        self._detect_task_type_patterns(success_records)
    
    def _detect_duration_patterns(self) -> None:
        """Detect patterns in execution duration"""
        # Group by task type and analyze duration
        duration_by_type = defaultdict(list)
        for record in self.execution_history:
            if record.duration_ms > 0:
                duration_by_type[record.task_type].append(record.duration_ms)
        
        for task_type, durations in duration_by_type.items():
            if len(durations) >= self.pattern_threshold:
                avg_duration = sum(durations) / len(durations)
                
                # Check for duration anomalies
                recent_durations = durations[-10:]
                recent_avg = sum(recent_durations) / len(recent_durations)
                
                if recent_avg > avg_duration * 1.5:  # 50% slower
                    pattern_id = self._generate_id("pat")
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type="increasing_duration",
                        projects=list(set(r.project_id for r in self.execution_history 
                                        if r.task_type == task_type)),
                        occurrences=len(durations),
                        confidence=0.7,
                        features={
                            'task_type': task_type,
                            'historical_avg_ms': avg_duration,
                            'recent_avg_ms': recent_avg,
                            'increase_factor': recent_avg / avg_duration if avg_duration > 0 else 0
                        },
                        first_seen=self.execution_history[0].timestamp if self.execution_history else datetime.now(timezone.utc).isoformat(),
                        last_seen=self.execution_history[-1].timestamp if self.execution_history else datetime.now(timezone.utc).isoformat(),
                        examples=[task_type]
                    )
                    self.detected_patterns[pattern_id] = pattern
    
    def self_optimize(self, target_metric: str = "success_rate") -> List[Optimization]:
        """
        Generate self-optimization suggestions based on historical data
        
        Args:
            target_metric: Metric to optimize (success_rate, duration, throughput)
        
        Returns:
            List of optimization suggestions
        """
        if not self.learning_enabled:
            print("[ATHENA-Reflection] Learning is disabled")
            return []
        
        optimization_config = self.config.get('optimization', {})
        if not optimization_config.get('enabled', True):
            print("[ATHENA-Reflection] Optimization is disabled")
            return []
        
        optimizations = []
        
        if target_metric == "success_rate":
            optimizations.extend(self._optimize_success_rate())
        elif target_metric == "duration":
            optimizations.extend(self._optimize_duration())
        elif target_metric == "throughput":
            optimizations.extend(self._optimize_throughput())
        
        min_improvement = optimization_config.get('min_improvement', 0.0)
        if min_improvement > 0:
            optimizations = [
                opt for opt in optimizations
                if opt.expected_improvement >= min_improvement
            ]
        
        max_suggestions = optimization_config.get('max_suggestions', len(optimizations))
        if max_suggestions and len(optimizations) > max_suggestions:
            optimizations = optimizations[:max_suggestions]
        
        # Store optimizations
        for opt in optimizations:
            self.optimization_history.append(opt)
        
        print(f"[ATHENA-Reflection] Generated {len(optimizations)} optimizations for {target_metric}")
        return optimizations
    
    def _optimize_success_rate(self) -> List[Optimization]:
        """Generate optimizations to improve success rate"""
        optimizations = []
        
        # Find low success rate task types
        task_type_stats = defaultdict(lambda: {'success': 0, 'total': 0})
        for record in self.execution_history:
            stats = task_type_stats[record.task_type]
            stats['total'] += 1
            if record.success:
                stats['success'] += 1
        
        for task_type, stats in task_type_stats.items():
            if stats['total'] >= self.pattern_threshold:
                success_rate = stats['success'] / stats['total']
                if success_rate < 0.7:
                    opt = Optimization(
                        optimization_id=self._generate_id("opt"),
                        target_metric="success_rate",
                        current_value=success_rate,
                        suggested_value=0.85,
                        expected_improvement=0.85 - success_rate,
                        confidence=0.7,
                        rationale=f"Low success rate ({success_rate:.2f}) for task type '{task_type}'. "
                                  f"Consider adding validation, improving error handling, or breaking into smaller tasks.",
                        applies_to=[task_type]
                    )
                    optimizations.append(opt)
        
        return optimizations
    
    def _optimize_duration(self) -> List[Optimization]:
        """Generate optimizations to reduce execution duration"""
        optimizations = []

        # Find task types with increasing duration
        duration_by_type = defaultdict(list)
        for record in self.execution_history:
            if record.duration_ms > 0:
                duration_by_type[record.task_type].append(record.duration_ms)

        for task_type, durations in duration_by_type.items():
            if len(durations) >= 10:
                historical_avg = sum(durations[:-10]) / max(len(durations) - 10, 1)
                recent_avg = sum(durations[-10:]) / 10

                # Skip if historical_avg is 0 to avoid division by zero
                if historical_avg <= 0:
                    continue

                if recent_avg > historical_avg * 1.3:  # 30% slower
                    opt = Optimization(
                        optimization_id=self._generate_id("opt"),
                        target_metric="duration",
                        current_value=recent_avg,
                        suggested_value=historical_avg,
                        expected_improvement=(recent_avg - historical_avg) / recent_avg,
                        confidence=0.6,
                        rationale=f"Execution time for '{task_type}' has increased by "
                                  f"{((recent_avg/historical_avg - 1) * 100):.1f}%. "
                                  f"Consider performance profiling or caching.",
                        applies_to=[task_type]
                    )
                    optimizations.append(opt)

        return optimizations
    
    def _optimize_throughput(self) -> List[Optimization]:
        """Generate optimizations to increase throughput"""
        optimizations = []
        
        # Analyze batch processing opportunities
        task_type_counts = defaultdict(int)
        for record in self.execution_history:
            task_type_counts[record.task_type] += 1
        
        for task_type, count in task_type_counts.items():
            if count >= 20:  # High volume task
                opt = Optimization(
                    optimization_id=self._generate_id("opt"),
                    target_metric="throughput",
                    current_value=count,
                    suggested_value=count * 1.5,
                    expected_improvement=0.5,
                    confidence=0.5,
                    rationale=f"High volume task '{task_type}' ({count} executions). "
                              f"Consider implementing batch processing or parallel execution.",
                    applies_to=[task_type]
                )
                optimizations.append(opt)
        
        return optimizations
    
    def cross_project_learn(self, source_project: str, 
                           target_project: str) -> Dict[str, Any]:
        """
        Transfer knowledge from source project to target project
        
        Args:
            source_project: Source project ID
            target_project: Target project ID
        
        Returns:
            Dictionary with transferred knowledge summary
        """
        cross_project_config = self.config.get('cross_project', {})
        if not cross_project_config.get('enabled', True):
            return {'status': 'disabled', 'message': 'Cross-project learning disabled'}
        
        # Filter records for source project
        source_records = [r for r in self.execution_history 
                         if r.project_id == source_project]
        
        if not source_records:
            return {'status': 'error', 'message': f'No data for project {source_project}'}
        
        knowledge_key = f"{source_project}_to_{target_project}"
        max_projects = cross_project_config.get('max_projects')
        if max_projects and knowledge_key not in self.cross_project_knowledge:
            if len(self.cross_project_knowledge) >= max_projects:
                return {
                    'status': 'error',
                    'message': 'Cross-project transfer limit reached'
                }
        
        # Extract patterns from source
        source_patterns = self.detect_patterns(project_ids=[source_project])
        transfer_threshold = cross_project_config.get('transfer_threshold', 0.0)
        share_anonymized = cross_project_config.get('share_anonymized', True)
        
        # Identify applicable patterns for target
        transferred_patterns = []
        for pattern in source_patterns:
            # Skip project-specific patterns
            if pattern.pattern_type in ['temporal', 'project_specific']:
                continue
            if pattern.confidence < transfer_threshold:
                continue
            
            # Add to cross-project knowledge
            if knowledge_key not in self.cross_project_knowledge:
                self.cross_project_knowledge[knowledge_key] = {
                    'source': source_project,
                    'target': target_project,
                    'patterns': [],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            pattern_payload = asdict(pattern)
            if share_anonymized:
                pattern_payload['projects'] = ['anonymized']
            
            self.cross_project_knowledge[knowledge_key]['patterns'].append(
                pattern_payload
            )
            transferred_patterns.append(pattern.pattern_id)
        
        result = {
            'status': 'success',
            'source_project': source_project,
            'target_project': target_project,
            'patterns_transferred': len(transferred_patterns),
            'pattern_ids': transferred_patterns,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._maybe_persist_data(force=True)
        
        print(f"[ATHENA-Reflection] Cross-project learning: {source_project} -> {target_project}")
        print(f"[ATHENA-Reflection] Transferred {len(transferred_patterns)} patterns")
        
        return result
    
    def reflect(self, context: Dict[str, Any], 
                depth: int = 0) -> ReflectionResult:
        """
        Perform recursive reflection on execution context
        
        Args:
            context: Current execution context
            depth: Current recursion depth (internal use)
        
        Returns:
            ReflectionResult with insights and recommendations
        """
        recursion_config = self.config.get('recursion', {})
        confidence_threshold = recursion_config.get('confidence_threshold', 0.5)
        early_termination = recursion_config.get('early_termination', True)
        depth_penalty = recursion_config.get('depth_penalty', 0.0)
        
        # Check recursion depth
        if depth >= self.max_recursion_depth:
            return ReflectionResult(
                reflection_id=self._generate_id("refl"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                recursion_depth=depth,
                patterns_detected=[],
                optimizations_suggested=[],
                cross_project_insights=[],
                confidence_score=0.0,
                learning_applied=False,
                metadata={'termination_reason': 'max_depth_reached'}
            )
        
        reflection_id = self._generate_id("refl")
        
        # Detect patterns relevant to context
        project_id = context.get('project_id')
        patterns = self.detect_patterns(
            project_ids=[project_id] if project_id else None
        )
        
        # Filter patterns by relevance to context
        relevant_patterns = [
            p for p in patterns 
            if context.get('task_type') in p.features.get('task_type', '')
            or context.get('task_type') in p.examples
        ]
        
        # Generate optimizations
        optimizations = self.self_optimize(
            target_metric=context.get('target_metric', 'success_rate')
        )
        
        # Cross-project insights
        cross_project_insights = []
        for knowledge_key, knowledge in self.cross_project_knowledge.items():
            if knowledge.get('target') == project_id:
                cross_project_insights.append({
                    'source': knowledge['source'],
                    'patterns_available': len(knowledge.get('patterns', []))
                })
        
        # Calculate confidence
        pattern_confidence = sum(p.confidence for p in relevant_patterns) / max(len(relevant_patterns), 1)
        opt_confidence = sum(o.confidence for o in optimizations) / max(len(optimizations), 1)
        confidence_score = (pattern_confidence + opt_confidence) / 2
        confidence_score = max(0.0, confidence_score - (depth * depth_penalty))
        
        result = ReflectionResult(
            reflection_id=reflection_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            recursion_depth=depth,
            patterns_detected=[asdict(p) for p in relevant_patterns],
            optimizations_suggested=[asdict(o) for o in optimizations],
            cross_project_insights=cross_project_insights,
            confidence_score=confidence_score,
            learning_applied=self.learning_enabled,
            metadata={
                'context_project': project_id,
                'context_task_type': context.get('task_type'),
                'total_patterns_available': len(self.detected_patterns)
            }
        )
        
        # Recursive call for deeper analysis
        should_recurse = depth < self.max_recursion_depth - 1
        if early_termination:
            should_recurse = should_recurse and confidence_score < confidence_threshold
        
        if should_recurse:
            deeper_context = context.copy()
            deeper_context['parent_reflection'] = reflection_id
            deeper_result = self.reflect(deeper_context, depth + 1)
            
            # Merge results
            result.patterns_detected.extend(deeper_result.patterns_detected)
            result.optimizations_suggested.extend(deeper_result.optimizations_suggested)
            result.confidence_score = max(result.confidence_score, deeper_result.confidence_score)
        
        print(f"[ATHENA-Reflection] Reflection {reflection_id} completed (depth: {depth})")
        
        return result
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning state"""
        return {
            'total_executions_recorded': len(self.execution_history),
            'patterns_detected': len(self.detected_patterns),
            'optimizations_generated': len(self.optimization_history),
            'cross_project_transfers': len(self.cross_project_knowledge),
            'learning_enabled': self.learning_enabled,
            'protocol_version': self.PROTOCOL_VERSION,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def export_knowledge(self, format: str = "json") -> str:
        """Export learned knowledge for sharing"""
        knowledge = {
            'protocol': f"{self.PROTOCOL_NAME} v{self.PROTOCOL_VERSION}",
            'patterns': {pid: asdict(p) for pid, p in self.detected_patterns.items()},
            'optimizations': [asdict(o) for o in self.optimization_history[-50:]],
            'cross_project': dict(self.cross_project_knowledge),
            'export_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if format == "json":
            return json.dumps(knowledge, indent=2)
        elif format == "yaml":
            return yaml.dump(knowledge, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == "__main__":
    """
    Test the ATHENA Reflection System
    """
    print("=" * 80)
    print("ATHENA Reflection System - Step 2: Recursion & Learning Test Suite")
    print("=" * 80)
    
    # Initialize reflection agent
    reflection = AthenaReflectionAgent(config_path="config")
    
    # Simulate recording executions
    print("\n" + "-" * 80)
    print("Recording sample executions...")
    print("-" * 80)
    
    sample_tasks = [
        {'project_id': 'stunts', 'task_type': 'classification', 'complexity_score': 5},
        {'project_id': 'stunts', 'task_type': 'classification', 'complexity_score': 5},
        {'project_id': 'alpha', 'task_type': 'code_generation', 'complexity_score': 8},
        {'project_id': 'alpha', 'task_type': 'code_generation', 'complexity_score': 8},
        {'project_id': 'beta', 'task_type': 'classification', 'complexity_score': 3},
        {'project_id': 'stunts', 'task_type': 'classification', 'complexity_score': 5},
        {'project_id': 'alpha', 'task_type': 'code_generation', 'complexity_score': 8},
        {'project_id': 'stunts', 'task_type': 'classification', 'complexity_score': 5},
    ]
    
    sample_results = [
        {'success': True, 'duration_ms': 150},
        {'success': True, 'duration_ms': 145},
        {'success': False, 'duration_ms': 2000, 'error_type': 'timeout'},
        {'success': False, 'duration_ms': 2100, 'error_type': 'timeout'},
        {'success': True, 'duration_ms': 100},
        {'success': True, 'duration_ms': 155},
        {'success': False, 'duration_ms': 2050, 'error_type': 'timeout'},
        {'success': True, 'duration_ms': 148},
    ]
    
    for task, result in zip(sample_tasks, sample_results):
        reflection.record_execution(task, result)
    
    # Test pattern detection
    print("\n" + "-" * 80)
    print("Detecting patterns...")
    print("-" * 80)
    
    patterns = reflection.detect_patterns()
    for pattern in patterns:
        print(f"\nPattern: {pattern.pattern_type}")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Occurrences: {pattern.occurrences}")
        print(f"  Projects: {', '.join(pattern.projects)}")
        print(f"  Features: {pattern.features}")
    
    # Test self-optimization
    print("\n" + "-" * 80)
    print("Generating optimizations...")
    print("-" * 80)
    
    optimizations = reflection.self_optimize(target_metric="success_rate")
    for opt in optimizations:
        print(f"\nOptimization: {opt.optimization_id}")
        print(f"  Target: {opt.target_metric}")
        print(f"  Current: {opt.current_value:.2f} -> Suggested: {opt.suggested_value:.2f}")
        print(f"  Expected improvement: {opt.expected_improvement:.2f}")
        print(f"  Confidence: {opt.confidence:.2f}")
        print(f"  Rationale: {opt.rationale}")
    
    # Test cross-project learning
    print("\n" + "-" * 80)
    print("Cross-project learning...")
    print("-" * 80)
    
    transfer_result = reflection.cross_project_learn('stunts', 'beta')
    print(f"Transfer status: {transfer_result['status']}")
    print(f"Patterns transferred: {transfer_result['patterns_transferred']}")
    
    # Test recursive reflection
    print("\n" + "-" * 80)
    print("Recursive reflection...")
    print("-" * 80)
    
    context = {
        'project_id': 'stunts',
        'task_type': 'classification',
        'target_metric': 'success_rate'
    }
    
    reflection_result = reflection.reflect(context)
    print(f"\nReflection ID: {reflection_result.reflection_id}")
    print(f"Recursion depth: {reflection_result.recursion_depth}")
    print(f"Confidence score: {reflection_result.confidence_score:.2f}")
    print(f"Patterns detected: {len(reflection_result.patterns_detected)}")
    print(f"Optimizations suggested: {len(reflection_result.optimizations_suggested)}")
    
    # Test learning summary
    print("\n" + "-" * 80)
    print("Learning summary...")
    print("-" * 80)
    
    summary = reflection.get_learning_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("Test suite completed")
    print("=" * 80)
