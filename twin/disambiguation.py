"""
Disambiguation Helper for Natural Language Queries
Provides context and entity resolution for the LLM to interpret queries
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import yaml
from pathlib import Path


class DisambiguationHelper:
    """
    Helps the LLM resolve ambiguous queries by providing:
    - Available entities and their current states
    - Valid parameter ranges and current values
    - Historical context and trends
    - Suggested clarifications to ask the user
    
    The LLM makes the final decisions - this just provides context
    """
    
    def __init__(self, db_path: str = "data/mes_database.db"):
        self.db_path = db_path
        self.nl_patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, Any]:
        """Load natural language patterns from YAML"""
        pattern_file = Path(__file__).parent / "nl_patterns.yaml"
        if pattern_file.exists():
            with open(pattern_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_query_context(self, query: str) -> Dict[str, Any]:
        """
        Provide context to help the LLM interpret a query
        
        Args:
            query: Natural language query from user
            
        Returns:
            Context dictionary with entities, suggestions, and metadata
        """
        context = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "entities": self._identify_entities(query),
            "timeframe": self._identify_timeframe(query),
            "available_data": self._get_available_data(),
            "current_state": self._get_current_state(),
            "parameter_hints": self._get_parameter_hints(query),
            "suggested_clarifications": self._suggest_clarifications(query)
        }
        
        return context
    
    def _identify_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Identify potential entities mentioned in the query
        Returns possibilities for the LLM to consider
        """
        query_lower = query.lower()
        entities = {
            "lines": [],
            "equipment": [],
            "shifts": [],
            "products": [],
            "metrics": []
        }
        
        # Check for line references
        if "line" in query_lower:
            entities["lines"] = ["LINE1", "LINE2", "LINE3"]
            # Check for specific line numbers
            for i in range(1, 4):
                if f"line {i}" in query_lower or f"line{i}" in query_lower:
                    entities["lines"] = [f"LINE{i}"]
                    break
        
        # Check for equipment references
        equipment_types = {
            "filler": "FIL",
            "packer": "PCK", 
            "palletizer": "PAL"
        }
        for equip_name, equip_code in equipment_types.items():
            if equip_name in query_lower:
                entities["equipment"].append(equip_code)
        
        # Check for shift references
        if "shift" in query_lower:
            entities["shifts"] = ["shift1", "shift2", "shift3"]
            for i in range(1, 4):
                if f"shift {i}" in query_lower or f"shift{i}" in query_lower:
                    entities["shifts"] = [f"shift{i}"]
                    break
        
        # Check for product references
        if any(word in query_lower for word in ["product", "sku", "energy drink", "juice"]):
            # Get available products from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT sku FROM production_orders LIMIT 10")
                entities["products"] = [row[0] for row in cursor.fetchall()]
        
        # Check for metrics
        metric_keywords = {
            "oee": ["oee", "overall equipment effectiveness"],
            "availability": ["availability", "uptime", "downtime"],
            "performance": ["performance", "speed", "throughput"],
            "quality": ["quality", "scrap", "defect", "yield"],
            "energy": ["energy", "power", "consumption"],
            "cost": ["cost", "expense", "financial"]
        }
        
        for metric, keywords in metric_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                entities["metrics"].append(metric)
        
        return entities
    
    def _identify_timeframe(self, query: str) -> Dict[str, Any]:
        """
        Identify temporal references in the query
        Returns suggestions for the LLM to consider
        """
        query_lower = query.lower()
        now = datetime.now()
        
        timeframe = {
            "explicit": None,
            "suggested": "last 7 days",
            "possibilities": []
        }
        
        # Check for explicit timeframes
        timeframe_patterns = {
            "today": (now.replace(hour=0, minute=0, second=0), now),
            "yesterday": (
                (now - timedelta(days=1)).replace(hour=0, minute=0, second=0),
                (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            ),
            "this week": (
                now - timedelta(days=now.weekday()),
                now
            ),
            "last week": (
                now - timedelta(days=now.weekday() + 7),
                now - timedelta(days=now.weekday())
            ),
            "this month": (
                now.replace(day=1, hour=0, minute=0, second=0),
                now
            ),
            "last month": (
                (now.replace(day=1) - timedelta(days=1)).replace(day=1),
                now.replace(day=1) - timedelta(seconds=1)
            )
        }
        
        for pattern, (start, end) in timeframe_patterns.items():
            if pattern in query_lower:
                timeframe["explicit"] = {
                    "pattern": pattern,
                    "start": start.isoformat(),
                    "end": end.isoformat()
                }
                break
        
        # Check for relative timeframes
        if "last" in query_lower:
            # Look for "last N days/weeks/hours"
            import re
            match = re.search(r"last (\d+) (hour|day|week|month)", query_lower)
            if match:
                number = int(match.group(1))
                unit = match.group(2)
                
                if unit == "hour":
                    delta = timedelta(hours=number)
                elif unit == "day":
                    delta = timedelta(days=number)
                elif unit == "week":
                    delta = timedelta(weeks=number)
                else:  # month
                    delta = timedelta(days=number * 30)
                
                timeframe["explicit"] = {
                    "pattern": match.group(0),
                    "start": (now - delta).isoformat(),
                    "end": now.isoformat()
                }
        
        # Add common possibilities for LLM to consider
        timeframe["possibilities"] = [
            "last 24 hours",
            "last 7 days",
            "last 30 days",
            "current shift",
            "since last maintenance"
        ]
        
        return timeframe
    
    def _get_available_data(self) -> Dict[str, Any]:
        """Get information about available data in the system"""
        with sqlite3.connect(self.db_path) as conn:
            available = {}
            
            # Get date range of data
            cursor = conn.execute("""
                SELECT MIN(created_at), MAX(created_at) 
                FROM equipment_signals
            """)
            row = cursor.fetchone()
            if row and row[0]:
                available["data_range"] = {
                    "start": row[0],
                    "end": row[1]
                }
            
            # Get available lines
            cursor = conn.execute("""
                SELECT DISTINCT line_id FROM equipment
            """)
            available["lines"] = [row[0] for row in cursor.fetchall()]
            
            # Get available equipment
            cursor = conn.execute("""
                SELECT DISTINCT equipment_id, equipment_type 
                FROM equipment
            """)
            available["equipment"] = [
                {"id": row[0], "type": row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Get recent simulation runs
            cursor = conn.execute("""
                SELECT run_id, run_type, started_at 
                FROM twin_runs 
                WHERE status = 'completed'
                ORDER BY started_at DESC 
                LIMIT 5
            """)
            available["recent_runs"] = [
                {"id": row[0], "type": row[1], "timestamp": row[2]}
                for row in cursor.fetchall()
            ]
            
            return available
    
    def _get_current_state(self) -> Dict[str, Any]:
        """Get current state of the virtual twin"""
        with sqlite3.connect(self.db_path) as conn:
            state = {}
            
            # Get current parameters from last run
            cursor = conn.execute("""
                SELECT config_delta_json 
                FROM twin_runs 
                WHERE status = 'completed'
                ORDER BY started_at DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row and row[0]:
                state["current_parameters"] = json.loads(row[0])
            
            # Get current KPIs
            cursor = conn.execute("""
                SELECT kpi_summary_json 
                FROM twin_runs 
                WHERE status = 'completed'
                ORDER BY started_at DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row and row[0]:
                state["current_kpis"] = json.loads(row[0])
            
            # Get sync health summary
            cursor = conn.execute("""
                SELECT health_status, COUNT(*) 
                FROM sync_health_dashboard 
                GROUP BY health_status
            """)
            state["sync_health"] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            return state
    
    def _get_parameter_hints(self, query: str) -> Dict[str, Any]:
        """
        Provide hints about parameters that might be relevant
        Based on natural language patterns
        """
        query_lower = query.lower()
        hints = {
            "likely_parameters": [],
            "suggested_values": {}
        }
        
        # Map keywords to parameters
        parameter_keywords = {
            "micro_stop_probability": ["micro-stop", "micro stop", "minor stop", "brief stop"],
            "performance_factor": ["speed", "throughput", "performance", "efficiency"],
            "scrap_multiplier": ["scrap", "waste", "quality", "defect", "reject"],
            "material_reliability": ["material", "supply", "starvation", "shortage"],
            "cascade_sensitivity": ["cascade", "downstream", "propagation", "coupling"]
        }
        
        for param, keywords in parameter_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                hints["likely_parameters"].append(param)
        
        # Suggest value changes based on intent
        if "improve" in query_lower or "better" in query_lower:
            hints["suggested_direction"] = "improvement"
            if "micro_stop_probability" in hints["likely_parameters"]:
                hints["suggested_values"]["micro_stop_probability"] = "reduce by 30-50%"
            if "scrap_multiplier" in hints["likely_parameters"]:
                hints["suggested_values"]["scrap_multiplier"] = "reduce by 20-40%"
        
        elif "degrade" in query_lower or "worse" in query_lower:
            hints["suggested_direction"] = "degradation"
            if "micro_stop_probability" in hints["likely_parameters"]:
                hints["suggested_values"]["micro_stop_probability"] = "increase by 50-100%"
        
        elif "optimal" in query_lower or "best" in query_lower:
            hints["suggested_direction"] = "optimization"
            hints["suggested_approach"] = "multi-objective optimization"
        
        return hints
    
    def _suggest_clarifications(self, query: str) -> List[str]:
        """
        Suggest clarifying questions the LLM might ask
        These are just suggestions - the LLM decides what to actually ask
        """
        suggestions = []
        query_lower = query.lower()
        
        # Check for ambiguous entity references
        if "line" in query_lower and not any(f"line {i}" in query_lower for i in range(1, 4)):
            suggestions.append("Which production line are you interested in? (LINE1, LINE2, or LINE3)")
        
        if "shift" in query_lower and not any(f"shift {i}" in query_lower for i in range(1, 4)):
            suggestions.append("Which shift period? (shift1: 6am-2pm, shift2: 2pm-10pm, shift3: 10pm-6am)")
        
        # Check for missing timeframe
        if not any(time_word in query_lower for time_word in 
                  ["today", "yesterday", "week", "month", "hour", "day"]):
            if "compare" in query_lower or "trend" in query_lower:
                suggestions.append("What time period should I analyze?")
        
        # Check for optimization without clear objectives
        if "optimize" in query_lower or "improve" in query_lower:
            if not any(metric in query_lower for metric in 
                      ["oee", "quality", "energy", "cost", "throughput"]):
                suggestions.append("What metrics should I optimize for?")
        
        # Check for vague comparisons
        if "better" in query_lower or "worse" in query_lower:
            suggestions.append("Compared to what baseline or reference?")
        
        return suggestions
    
    def resolve_entity(self, entity_type: str, entity_ref: str) -> Optional[str]:
        """
        Resolve an entity reference to its canonical form
        This is deterministic resolution for clear cases
        
        Args:
            entity_type: Type of entity (line, equipment, etc.)
            entity_ref: Reference string from query
            
        Returns:
            Canonical entity ID or None if ambiguous
        """
        ref_lower = entity_ref.lower().strip()
        
        if entity_type == "line":
            # Direct mappings
            if ref_lower in ["line 1", "line1", "l1", "first line"]:
                return "LINE1"
            elif ref_lower in ["line 2", "line2", "l2", "second line"]:
                return "LINE2"
            elif ref_lower in ["line 3", "line3", "l3", "third line"]:
                return "LINE3"
        
        elif entity_type == "equipment":
            if "fill" in ref_lower:
                return "FIL"
            elif "pack" in ref_lower:
                return "PCK"
            elif "pallet" in ref_lower:
                return "PAL"
        
        elif entity_type == "shift":
            if ref_lower in ["shift 1", "shift1", "morning", "first shift"]:
                return "shift1"
            elif ref_lower in ["shift 2", "shift2", "afternoon", "second shift"]:
                return "shift2"
            elif ref_lower in ["shift 3", "shift3", "night", "third shift"]:
                return "shift3"
        
        return None


def demonstrate_disambiguation():
    """Demonstrate disambiguation helper"""
    print("DISAMBIGUATION HELPER DEMONSTRATION")
    print("=" * 60)
    
    helper = DisambiguationHelper()
    
    # Test various ambiguous queries
    test_queries = [
        "What's the impact of better maintenance?",
        "Why is Line 2 outperforming others?",
        "Optimize for energy efficiency",
        "Compare shifts this week",
        "Find the bottleneck",
        "Improve quality on the packer"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        context = helper.get_query_context(query)
        
        # Show identified entities
        if any(context["entities"].values()):
            print("Identified entities:")
            for entity_type, entities in context["entities"].items():
                if entities:
                    print(f"  {entity_type}: {entities}")
        
        # Show parameter hints
        if context["parameter_hints"]["likely_parameters"]:
            print(f"Likely parameters: {context['parameter_hints']['likely_parameters']}")
        
        # Show suggestions
        if context["suggested_clarifications"]:
            print("Suggested clarifications:")
            for suggestion in context["suggested_clarifications"]:
                print(f"  - {suggestion}")
        
        # Show timeframe
        if context["timeframe"]["explicit"]:
            print(f"Timeframe: {context['timeframe']['explicit']['pattern']}")
        else:
            print(f"Default timeframe: {context['timeframe']['suggested']}")
    
    print("\n✅ Disambiguation helper demonstrated!")
    print("\nNote: The LLM makes final decisions - this just provides context")


if __name__ == "__main__":
    demonstrate_disambiguation()