"""
Compliance and Safety Layer for Phase 3

Ensures regulatory compliance and safety in query processing and response generation.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict
from enum import Enum

from .query_classifier import QueryClassification, QueryType
from .response_generator import GeneratedResponse

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceCheck:
    """Compliance check result."""
    check_type: str
    passed: bool
    risk_level: RiskLevel
    details: str
    recommendations: List[str]
    timestamp: datetime

@dataclass
class SafetyCheck:
    """Safety check result."""
    check_type: str
    passed: bool
    risk_level: RiskLevel
    details: str
    blocked_content: List[str]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class ComplianceResult:
    """Overall compliance result."""
    query: str
    classification: QueryClassification
    response: GeneratedResponse
    compliance_checks: List[ComplianceCheck]
    safety_checks: List[SafetyCheck]
    overall_risk: RiskLevel
    approved: bool
    modifications: List[str]
    timestamp: datetime

class ComplianceSafetyLayer:
    """
    Ensures regulatory compliance and safety in query processing and response generation.
    
    Features:
    - Regulatory compliance checks
    - Content safety validation
    - Risk assessment
    - Content filtering
    - Compliance reporting
    - Audit trail maintenance
    """
    
    def __init__(self, cache_dir: str = "cache/compliance_safety"):
        """
        Initialize compliance and safety layer.
        
        Args:
            cache_dir: Directory for caching compliance data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Compliance rules
        self.compliance_rules = self._initialize_compliance_rules()
        
        # Safety rules
        self.safety_rules = self._initialize_safety_rules()
        
        # Blocked content patterns
        self.blocked_patterns = self._initialize_blocked_patterns()
        
        # Compliance statistics
        self.compliance_stats = defaultdict(int)
        self.compliance_history: List[ComplianceResult] = []
        
        # Configuration
        self.max_risk_level = RiskLevel.HIGH
        self.auto_approve_threshold = RiskLevel.MEDIUM
        
        # Load existing data
        self._load_rules()
        self._load_stats()
        
        logger.info("Compliance and Safety Layer initialized")
    
    def _initialize_compliance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance rules."""
        return {
            "investment_advice": {
                "description": "Prevent giving investment advice",
                "patterns": [
                    r"should.*invest",
                    r"recommend.*fund",
                    r"best.*fund",
                    r"good.*investment",
                    r"buy.*fund",
                    r"sell.*fund"
                ],
                "risk_level": RiskLevel.HIGH,
                "action": "block_or_redirect",
                "allowed_responses": ["educational", "general_info", "disclaimer"]
            },
            "financial_guarantees": {
                "description": "Prevent making financial guarantees",
                "patterns": [
                    r"guaranteed.*return",
                    r"sure.*profit",
                    r"no.*risk",
                    r"safe.*investment",
                    r"guarantee.*profit",
                    r"certain.*return"
                ],
                "risk_level": RiskLevel.CRITICAL,
                "action": "block",
                "allowed_responses": []
            },
            "comparative_ranking": {
                "description": "Prevent ranking funds",
                "patterns": [
                    r"#1.*fund",
                    r"best.*performing",
                    r"top.*ranked",
                    r"highest.*return",
                    r"worst.*fund",
                    r"lowest.*return"
                ],
                "risk_level": RiskLevel.MEDIUM,
                "action": "modify",
                "allowed_responses": ["factual_comparison", "neutral_comparison"]
            },
            "tax_advice": {
                "description": "Prevent giving tax advice",
                "patterns": [
                    r"tax.*advice",
                    r"save.*tax",
                    r"tax.*benefit",
                    r"tax.*saving",
                    r"tax.*planning"
                ],
                "risk_level": RiskLevel.HIGH,
                "action": "redirect",
                "allowed_responses": ["general_tax_info", "consult_professional"]
            },
            "legal_advice": {
                "description": "Prevent giving legal advice",
                "patterns": [
                    r"legal.*advice",
                    r"legal.*recommendation",
                    r"court.*case",
                    r"legal.*action",
                    r"sue.*fund"
                ],
                "risk_level": RiskLevel.CRITICAL,
                "action": "block",
                "allowed_responses": []
            }
        }
    
    def _initialize_safety_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safety rules."""
        return {
            "personal_information": {
                "description": "Protect personal information",
                "patterns": [
                    r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card numbers
                    r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",  # SSN pattern
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"  # Email addresses
                ],
                "risk_level": RiskLevel.CRITICAL,
                "action": "redact"
            },
            "inappropriate_content": {
                "description": "Block inappropriate content",
                "patterns": [
                    r"\b(hate|racist|discriminatory|offensive)\b",
                    r"\b(violent|threat|harm|dangerous)\b",
                    r"\b(illegal|criminal|fraud|scam)\b"
                ],
                "risk_level": RiskLevel.HIGH,
                "action": "block"
            },
            "misinformation": {
                "description": "Prevent spreading misinformation",
                "patterns": [
                    r"\b(fake|false|misleading|unverified)\b.*\b(return|profit|guarantee)\b",
                    r"\b(certain|guaranteed|sure).*\b(profit|return|gain)\b"
                ],
                "risk_level": RiskLevel.HIGH,
                "action": "modify"
            },
            "sensitive_topics": {
                "description": "Handle sensitive topics carefully",
                "patterns": [
                    r"\b(political|religion|controversial)\b",
                    r"\b(scandal|controversy|lawsuit)\b"
                ],
                "risk_level": RiskLevel.MEDIUM,
                "action": "redirect"
            }
        }
    
    def _initialize_blocked_patterns(self) -> List[str]:
        """Initialize blocked content patterns."""
        return [
            # Investment advice patterns
            r"buy.*now",
            r"sell.*now",
            r"invest.*immediately",
            r"guaranteed.*profit",
            r"risk.*free.*return",
            
            # Financial guarantee patterns
            r"100%.*safe",
            r"no.*risk.*investment",
            r"certain.*return",
            r"guaranteed.*success",
            
            # Inappropriate content
            r"\b(hate|racist)\b",
            r"\b(violent|threat)\b",
            r"\b(illegal|criminal)\b"
        ]
    
    def _load_rules(self) -> None:
        """Load rules from cache."""
        rules_file = self.cache_dir / "rules.json"
        
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    data = json.load(f)
                
                # Convert risk levels back to enums
                for rule_type, rules in data.get("compliance_rules", {}).items():
                    if rule_type in self.compliance_rules:
                        self.compliance_rules[rule_type]["risk_level"] = RiskLevel(rules["risk_level"])
                
                for rule_type, rules in data.get("safety_rules", {}).items():
                    if rule_type in self.safety_rules:
                        self.safety_rules[rule_type]["risk_level"] = RiskLevel(rules["risk_level"])
                
                logger.info(f"Loaded compliance and safety rules")
                
            except Exception as e:
                logger.error(f"Error loading rules: {e}")
    
    def _load_stats(self) -> None:
        """Load compliance statistics from cache."""
        stats_file = self.cache_dir / "stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                
                self.compliance_stats = defaultdict(int, data.get("compliance_stats", {}))
                
                # Load compliance history
                history_data = data.get("compliance_history", [])
                self.compliance_history = []
                for item in history_data:
                    item['classification']['query_type'] = QueryType(item['classification']['query_type'])
                    item['overall_risk'] = RiskLevel(item['overall_risk'])
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    
                    # Convert compliance checks
                    compliance_checks = []
                    for check in item['compliance_checks']:
                        check['risk_level'] = RiskLevel(check['risk_level'])
                        check['timestamp'] = datetime.fromisoformat(check['timestamp'])
                        compliance_checks.append(ComplianceCheck(**check))
                    
                    # Convert safety checks
                    safety_checks = []
                    for check in item['safety_checks']:
                        check['risk_level'] = RiskLevel(check['risk_level'])
                        check['timestamp'] = datetime.fromisoformat(check['timestamp'])
                        safety_checks.append(SafetyCheck(**check))
                    
                    item['compliance_checks'] = compliance_checks
                    item['safety_checks'] = safety_checks
                    self.compliance_history.append(ComplianceResult(**item))
                
                logger.info(f"Loaded compliance statistics")
                
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
    
    def _save_rules(self) -> None:
        """Save rules to cache."""
        try:
            rules_file = self.cache_dir / "rules.json"
            
            # Convert risk levels to strings for JSON serialization
            serializable_rules = {
                "compliance_rules": {},
                "safety_rules": {}
            }
            
            for rule_type, rule in self.compliance_rules.items():
                serializable_rules["compliance_rules"][rule_type] = rule.copy()
                serializable_rules["compliance_rules"][rule_type]["risk_level"] = rule["risk_level"].value
            
            for rule_type, rule in self.safety_rules.items():
                serializable_rules["safety_rules"][rule_type] = rule.copy()
                serializable_rules["safety_rules"][rule_type]["risk_level"] = rule["risk_level"].value
            
            with open(rules_file, 'w') as f:
                json.dump(serializable_rules, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
    
    def _save_stats(self) -> None:
        """Save compliance statistics to cache."""
        try:
            stats_file = self.cache_dir / "stats.json"
            
            serializable_history = []
            for result in self.compliance_history:
                result_dict = asdict(result)
                result_dict['classification']['query_type'] = result.classification.query_type.value
                result_dict['overall_risk'] = result.overall_risk.value
                result_dict['timestamp'] = result.timestamp.isoformat()
                
                # Convert compliance checks
                serializable_compliance = []
                for check in result.compliance_checks:
                    check_dict = asdict(check)
                    check_dict['risk_level'] = check.risk_level.value
                    check_dict['timestamp'] = check.timestamp.isoformat()
                    serializable_compliance.append(check_dict)
                
                # Convert safety checks
                serializable_safety = []
                for check in result.safety_checks:
                    check_dict = asdict(check)
                    check_dict['risk_level'] = check.risk_level.value
                    check_dict['timestamp'] = check.timestamp.isoformat()
                    serializable_safety.append(check_dict)
                
                result_dict['compliance_checks'] = serializable_compliance
                result_dict['safety_checks'] = serializable_safety
                serializable_history.append(result_dict)
            
            data = {
                "compliance_stats": dict(self.compliance_stats),
                "compliance_history": serializable_history[-1000]  # Keep last 1000
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    async def check_compliance(self, query: str, classification: QueryClassification, 
                            response: GeneratedResponse) -> ComplianceResult:
        """
        Perform comprehensive compliance and safety checks.
        
        Args:
            query: Original query
            classification: Query classification
            response: Generated response
            
        Returns:
            ComplianceResult object
        """
        logger.info(f"Performing compliance check for: {query[:100]}...")
        
        # Perform compliance checks
        compliance_checks = await self._perform_compliance_checks(query, classification, response)
        
        # Perform safety checks
        safety_checks = await self._perform_safety_checks(query, response)
        
        # Determine overall risk level
        overall_risk = self._calculate_overall_risk(compliance_checks, safety_checks)
        
        # Determine if response is approved
        approved = self._determine_approval(overall_risk, compliance_checks, safety_checks)
        
        # Apply modifications if needed
        modifications = []
        if not approved:
            modifications = self._generate_modifications(compliance_checks, safety_checks)
            response = self._apply_modifications(response, modifications)
        
        # Create compliance result
        compliance_result = ComplianceResult(
            query=query,
            classification=classification,
            response=response,
            compliance_checks=compliance_checks,
            safety_checks=safety_checks,
            overall_risk=overall_risk,
            approved=approved,
            modifications=modifications,
            timestamp=datetime.now()
        )
        
        # Update statistics
        self.compliance_stats[f"risk_{overall_risk.value}"] += 1
        self.compliance_stats[f"approved_{approved}"] += 1
        self.compliance_history.append(compliance_result)
        
        # Save updated stats
        if len(self.compliance_history) % 10 == 0:
            self._save_stats()
        
        logger.info(f"Compliance check completed: {overall_risk.value} risk, approved: {approved}")
        
        return compliance_result
    
    async def _perform_compliance_checks(self, query: str, classification: QueryClassification, 
                                       response: GeneratedResponse) -> List[ComplianceCheck]:
        """Perform compliance checks."""
        checks = []
        
        for rule_name, rule in self.compliance_rules.items():
            check = await self._check_compliance_rule(rule_name, rule, query, classification, response)
            checks.append(check)
        
        return checks
    
    async def _perform_safety_checks(self, query: str, response: GeneratedResponse) -> List[SafetyCheck]:
        """Perform safety checks."""
        checks = []
        
        for rule_name, rule in self.safety_rules.items():
            check = await self._check_safety_rule(rule_name, rule, query, response)
            checks.append(check)
        
        # Check blocked patterns
        blocked_check = await self._check_blocked_patterns(query, response)
        checks.append(blocked_check)
        
        return checks
    
    async def _check_compliance_rule(self, rule_name: str, rule: Dict[str, Any], 
                                   query: str, classification: QueryClassification, 
                                   response: GeneratedResponse) -> ComplianceCheck:
        """Check a specific compliance rule."""
        patterns = rule.get("patterns", [])
        risk_level = rule.get("risk_level", RiskLevel.MEDIUM)
        
        # Check query and response for patterns
        matches = []
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches.append(f"Query: {pattern}")
            if re.search(pattern, response.content, re.IGNORECASE):
                matches.append(f"Response: {pattern}")
        
        passed = len(matches) == 0
        
        if not passed:
            details = f"Compliance rule '{rule_name}' violated by: {', '.join(matches)}"
            recommendations = self._get_compliance_recommendations(rule_name, rule)
        else:
            details = f"Compliance rule '{rule_name}' passed"
            recommendations = []
        
        return ComplianceCheck(
            check_type=rule_name,
            passed=passed,
            risk_level=risk_level,
            details=details,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    async def _check_safety_rule(self, rule_name: str, rule: Dict[str, Any], 
                               query: str, response: GeneratedResponse) -> SafetyCheck:
        """Check a specific safety rule."""
        patterns = rule.get("patterns", [])
        risk_level = rule.get("risk_level", RiskLevel.MEDIUM)
        
        # Check query and response for patterns
        matches = []
        blocked_content = []
        
        for pattern in patterns:
            query_matches = re.findall(pattern, query, re.IGNORECASE)
            response_matches = re.findall(pattern, response.content, re.IGNORECASE)
            
            if query_matches:
                matches.extend([f"Query: {match}" for match in query_matches])
                blocked_content.extend(query_matches)
            
            if response_matches:
                matches.extend([f"Response: {match}" for match in response_matches])
                blocked_content.extend(response_matches)
        
        passed = len(matches) == 0
        
        if not passed:
            details = f"Safety rule '{rule_name}' violated by: {', '.join(matches)}"
            recommendations = self._get_safety_recommendations(rule_name, rule)
        else:
            details = f"Safety rule '{rule_name}' passed"
            recommendations = []
        
        return SafetyCheck(
            check_type=rule_name,
            passed=passed,
            risk_level=risk_level,
            details=details,
            blocked_content=blocked_content,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    async def _check_blocked_patterns(self, query: str, response: GeneratedResponse) -> SafetyCheck:
        """Check for blocked patterns."""
        matches = []
        blocked_content = []
        
        for pattern in self.blocked_patterns:
            query_matches = re.findall(pattern, query, re.IGNORECASE)
            response_matches = re.findall(pattern, response.content, re.IGNORECASE)
            
            if query_matches:
                matches.extend([f"Query: {match}" for match in query_matches])
                blocked_content.extend(query_matches)
            
            if response_matches:
                matches.extend([f"Response: {match}" for match in response_matches])
                blocked_content.extend(response_matches)
        
        passed = len(matches) == 0
        
        if not passed:
            details = f"Blocked patterns detected: {', '.join(matches)}"
            recommendations = ["Remove or modify blocked content", "Use alternative phrasing"]
        else:
            details = "No blocked patterns detected"
            recommendations = []
        
        return SafetyCheck(
            check_type="blocked_patterns",
            passed=passed,
            risk_level=RiskLevel.CRITICAL if not passed else RiskLevel.LOW,
            details=details,
            blocked_content=blocked_content,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    def _calculate_overall_risk(self, compliance_checks: List[ComplianceCheck], 
                                safety_checks: List[SafetyCheck]) -> RiskLevel:
        """Calculate overall risk level."""
        all_checks = compliance_checks + safety_checks
        
        if not all_checks:
            return RiskLevel.LOW
        
        # Find the highest risk level among failed checks
        failed_checks = [check for check in all_checks if not check.passed]
        
        if not failed_checks:
            return RiskLevel.LOW
        
        # Return the highest risk level
        risk_levels = [check.risk_level for check in failed_checks]
        
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_approval(self, overall_risk: RiskLevel, 
                          compliance_checks: List[ComplianceCheck], 
                          safety_checks: List[SafetyCheck]) -> bool:
        """Determine if response is approved."""
        # Auto-reject if risk level is too high
        if overall_risk == RiskLevel.CRITICAL:
            return False
        
        # Auto-reject if any critical compliance checks failed
        critical_failures = [
            check for check in compliance_checks 
            if not check.passed and check.risk_level == RiskLevel.CRITICAL
        ]
        if critical_failures:
            return False
        
        # Auto-reject if any critical safety checks failed
        critical_safety_failures = [
            check for check in safety_checks 
            if not check.passed and check.risk_level == RiskLevel.CRITICAL
        ]
        if critical_safety_failures:
            return False
        
        # Auto-approve if risk level is below threshold
        if overall_risk.value in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]:
            return True
        
        # For high risk, require manual review (reject for now)
        return False
    
    def _generate_modifications(self, compliance_checks: List[ComplianceCheck], 
                               safety_checks: List[SafetyCheck]) -> List[str]:
        """Generate modifications for failed checks."""
        modifications = []
        
        all_checks = compliance_checks + safety_checks
        failed_checks = [check for check in all_checks if not check.passed]
        
        for check in failed_checks:
            if check.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                modifications.extend(check.recommendations)
        
        return list(set(modifications))  # Remove duplicates
    
    def _apply_modifications(self, response: GeneratedResponse, modifications: List[str]) -> GeneratedResponse:
        """Apply modifications to response."""
        modified_content = response.content
        
        # Add disclaimer for investment advice
        if any("investment advice" in mod.lower() for mod in modifications):
            modified_content += "\n\n⚠️ This information is for educational purposes only and should not be considered as investment advice. Please consult a qualified financial advisor for personalized recommendations."
        
        # Add general disclaimer
        if any("disclaimer" in mod.lower() for mod in modifications):
            modified_content += "\n\nDisclaimer: This response is provided for informational purposes only and does not constitute financial, legal, or tax advice."
        
        # Redact sensitive information
        if any("redact" in mod.lower() for mod in modifications):
            modified_content = self._redact_sensitive_info(modified_content)
        
        # Create modified response
        modified_response = GeneratedResponse(
            query=response.query,
            response_type=response.response_type,
            content=modified_content,
            sources=response.sources,
            confidence=response.confidence * 0.8,  # Reduce confidence due to modifications
            response_time=response.response_time,
            metadata={
                **response.metadata,
                "modifications_applied": modifications,
                "original_content": response.content
            }
        )
        
        return modified_response
    
    def _redact_sensitive_info(self, content: str) -> str:
        """Redact sensitive information from content."""
        # Redact email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', content)
        
        # Redact phone numbers
        content = re.sub(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b', '[REDACTED]', content)
        
        # Redact credit card numbers
        content = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED]', content)
        
        # Redact SSN patterns
        content = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[REDACTED]', content)
        
        return content
    
    def _get_compliance_recommendations(self, rule_name: str, rule: Dict[str, Any]) -> List[str]:
        """Get recommendations for compliance rule violations."""
        action = rule.get("action", "block")
        allowed_responses = rule.get("allowed_responses", [])
        
        recommendations = []
        
        if action == "block":
            recommendations.append("Response blocked due to compliance violation")
        elif action == "redirect":
            recommendations.append("Redirect to educational content")
        elif action == "modify":
            recommendations.append("Modify response to comply with regulations")
        
        if allowed_responses:
            recommendations.append(f"Allowed response types: {', '.join(allowed_responses)}")
        
        return recommendations
    
    def _get_safety_recommendations(self, rule_name: str, rule: Dict[str, Any]) -> List[str]:
        """Get recommendations for safety rule violations."""
        action = rule.get("action", "block")
        
        recommendations = []
        
        if action == "block":
            recommendations.append("Content blocked due to safety concerns")
        elif action == "redact":
            recommendations.append("Redact sensitive information")
        elif action == "modify":
            recommendations.append("Modify content to ensure safety")
        elif action == "redirect":
            recommendations.append("Redirect to safer content")
        
        return recommendations
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """
        Get compliance statistics.
        
        Returns:
            Compliance statistics dictionary
        """
        total_checks = sum(self.compliance_stats.values())
        
        # Calculate risk distribution
        risk_distribution = {}
        for key, count in self.compliance_stats.items():
            if key.startswith("risk_"):
                risk_level = key.replace("risk_", "")
                risk_distribution[risk_level] = {
                    "count": count,
                    "percentage": (count / total_checks * 100) if total_checks > 0 else 0
                }
        
        # Calculate approval rate
        approved_count = self.compliance_stats.get("approved_True", 0)
        approval_rate = (approved_count / total_checks * 100) if total_checks > 0 else 0
        
        # Recent trends (last 100 checks)
        recent_checks = self.compliance_history[-100:] if self.compliance_history else []
        recent_risks = [check.overall_risk.value for check in recent_checks]
        
        return {
            "total_checks": total_checks,
            "risk_distribution": risk_distribution,
            "approval_rate": approval_rate,
            "compliance_rules_count": len(self.compliance_rules),
            "safety_rules_count": len(self.safety_rules),
            "blocked_patterns_count": len(self.blocked_patterns),
            "recent_trends": {
                "total_recent": len(recent_checks),
                "risk_distribution": {
                    risk: recent_risks.count(risk) for risk in set(recent_risks)
                }
            }
        }
    
    def get_compliance_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate compliance report for specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Compliance report dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent compliance results
        recent_results = [
            result for result in self.compliance_history
            if result.timestamp > cutoff_date
        ]
        
        if not recent_results:
            return {"message": f"No compliance data available for the last {days} days"}
        
        # Calculate statistics
        total_checks = len(recent_results)
        approved_count = len([r for r in recent_results if r.approved])
        
        risk_distribution = defaultdict(int)
        rule_violations = defaultdict(int)
        
        for result in recent_results:
            risk_distribution[result.overall_risk.value] += 1
            
            # Count rule violations
            for check in result.compliance_checks + result.safety_checks:
                if not check.passed:
                    rule_violations[check.check_type] += 1
        
        return {
            "period_days": days,
            "total_checks": total_checks,
            "approved_responses": approved_count,
            "approval_rate": (approved_count / total_checks * 100) if total_checks > 0 else 0,
            "risk_distribution": dict(risk_distribution),
            "top_violations": sorted(rule_violations.items(), key=lambda x: x[1], reverse=True)[:10],
            "most_common_risk": max(risk_distribution.items(), key=lambda x: x[1])[0] if risk_distribution else "low"
        }
    
    def add_compliance_rule(self, rule_name: str, description: str, patterns: List[str],
                          risk_level: RiskLevel, action: str, allowed_responses: List[str] = None) -> None:
        """
        Add a custom compliance rule.
        
        Args:
            rule_name: Rule name
            description: Rule description
            patterns: Regex patterns to match
            risk_level: Risk level
            action: Action to take
            allowed_responses: Allowed response types
        """
        self.compliance_rules[rule_name] = {
            "description": description,
            "patterns": patterns,
            "risk_level": risk_level,
            "action": action,
            "allowed_responses": allowed_responses or []
        }
        
        self._save_rules()
        
        logger.info(f"Added compliance rule: {rule_name}")
    
    def remove_compliance_rule(self, rule_name: str) -> bool:
        """
        Remove a compliance rule.
        
        Args:
            rule_name: Rule name to remove
            
        Returns:
            True if rule was removed
        """
        if rule_name in self.compliance_rules:
            del self.compliance_rules[rule_name]
            self._save_rules()
            
            logger.info(f"Removed compliance rule: {rule_name}")
            return True
        
        return False
    
    def add_safety_rule(self, rule_name: str, description: str, patterns: List[str],
                       risk_level: RiskLevel, action: str) -> None:
        """
        Add a custom safety rule.
        
        Args:
            rule_name: Rule name
            description: Rule description
            patterns: Regex patterns to match
            risk_level: Risk level
            action: Action to take
        """
        self.safety_rules[rule_name] = {
            "description": description,
            "patterns": patterns,
            "risk_level": risk_level,
            "action": action
        }
        
        self._save_rules()
        
        logger.info(f"Added safety rule: {rule_name}")
    
    def remove_safety_rule(self, rule_name: str) -> bool:
        """
        Remove a safety rule.
        
        Args:
            rule_name: Rule name to remove
            
        Returns:
            True if rule was removed
        """
        if rule_name in self.safety_rules:
            del self.safety_rules[rule_name]
            self._save_rules()
            
            logger.info(f"Removed safety rule: {rule_name}")
            return True
        
        return False
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old compliance data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of items cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old compliance history
        old_results = [
            result for result in self.compliance_history
            if result.timestamp < cutoff_date
        ]
        
        self.compliance_history = [
            result for result in self.compliance_history
            if result.timestamp >= cutoff_date
        ]
        
        # Save updated data
        self._save_stats()
        
        logger.info(f"Cleaned up {len(old_results)} old compliance records")
        return len(old_results)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on compliance and safety layer.
        
        Returns:
            Health status dictionary
        """
        stats = self.get_compliance_stats()
        
        health_status = {
            "status": "healthy",
            "issues": [],
            "details": {
                "compliance_rules": stats["compliance_rules_count"],
                "safety_rules": stats["safety_rules_count"],
                "total_checks": stats["total_checks"],
                "approval_rate": stats["approval_rate"],
                "risk_distribution": dict(stats["risk_distribution"])
            }
        }
        
        # Check if we have enough rules
        if stats["compliance_rules_count"] < 3:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient compliance rules")
        
        if stats["safety_rules_count"] < 2:
            health_status["status"] = "degraded"
            health_status["issues"].append("Insufficient safety rules")
        
        # Check approval rate
        if stats["approval_rate"] < 70:
            health_status["status"] = "degraded"
            health_status["issues"].append("Low approval rate")
        
        return health_status
