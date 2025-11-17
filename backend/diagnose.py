#!/usr/bin/env python3
"""
MISIX System Diagnostics Script

This script performs comprehensive diagnostics of the MISIX system including:
- Environment variables
- Database connection and schema
- Bot initialization
- Handlers registration
- AI service availability

Usage:
    python3 diagnose.py
"""

import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    component: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        emoji = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(self.status, "❓")
        return f"{emoji} {self.component}: {self.message}"


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""
    results: List[DiagnosticResult]
    overall_status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# MISIX System Diagnostic Report",
            f"\n**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n**Overall Status:** {self.overall_status}\n",
            "## Component Status\n"
        ]
        
        for result in self.results:
            lines.append(str(result))
            if result.details:
                for key, value in result.details.items():
                    lines.append(f"  - {key}: {value}")
            lines.append("")
        
        if self.recommendations:
            lines.append("\n## Recommendations\n")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)


class SystemDiagnostics:
    """System diagnostics runner."""
    
    def __init__(self):
        self.results: List[DiagnosticResult] = []
        self.recommendations: List[str] = []
    
    async def check_environment(self) -> DiagnosticResult:
        """Check environment variables."""
        print("🔍 Checking environment variables...")
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "YANDEX_GPT_API_KEY",
            "YANDEX_FOLDER_ID",
            "JWT_SECRET_KEY"
        ]
        
        missing = []
        present = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                present.append(var)
            else:
                missing.append(var)
        
        if missing:
            return DiagnosticResult(
                component="Environment Variables",
                status="ERROR",
                message=f"Missing {len(missing)} required variables",
                details={
                    "missing": missing,
                    "present": present
                }
            )
        
        return DiagnosticResult(
            component="Environment Variables",
            status="OK",
            message=f"All {len(required_vars)} required variables present",
            details={"variables": present}
        )
    
    async def check_database(self) -> DiagnosticResult:
        """Check database connection."""
        print("🔍 Checking database connection...")
        
        try:
            from app.shared.supabase import get_supabase_client
            
            client = get_supabase_client()
            
            # Try a simple query
            result = client.table("users").select("id").limit(1).execute()
            
            return DiagnosticResult(
                component="Database Connection",
                status="OK",
                message="Successfully connected to Supabase",
                details={
                    "url": os.getenv("SUPABASE_URL", "")[:30] + "...",
                    "test_query": "SELECT id FROM users LIMIT 1"
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="Database Connection",
                status="ERROR",
                message=f"Failed to connect: {str(e)[:100]}",
                details={"error": str(e)}
            )
    
    async def check_database_schema(self) -> DiagnosticResult:
        """Check database schema and tables."""
        print("🔍 Checking database schema...")
        
        required_tables = [
            "users",
            "tasks",
            "finance_entries",
            "notes",
            "note_folders",
            "mood_entries",
            "assistant_messages",
            "user_settings",
            "sleep_tracking",
            "personal_entries"
        ]
        
        try:
            from app.shared.supabase import get_supabase_client
            
            client = get_supabase_client()
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                try:
                    # Try to query the table
                    client.table(table).select("*").limit(1).execute()
                    existing_tables.append(table)
                except Exception:
                    missing_tables.append(table)
            
            if missing_tables:
                return DiagnosticResult(
                    component="Database Schema",
                    status="ERROR",
                    message=f"Missing {len(missing_tables)} tables",
                    details={
                        "missing": missing_tables,
                        "existing": existing_tables
                    }
                )
            
            return DiagnosticResult(
                component="Database Schema",
                status="OK",
                message=f"All {len(required_tables)} required tables exist",
                details={"tables": existing_tables}
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="Database Schema",
                status="ERROR",
                message=f"Failed to check schema: {str(e)[:100]}",
                details={"error": str(e)}
            )
    
    async def check_bot_initialization(self) -> DiagnosticResult:
        """Check bot initialization."""
        print("🔍 Checking bot initialization...")
        
        try:
            from app.bot import get_application
            
            app = get_application()
            
            if app is None:
                return DiagnosticResult(
                    component="Bot Initialization",
                    status="ERROR",
                    message="Bot application is None",
                    details={"reason": "Token not configured or initialization failed"}
                )
            
            # Check if bot is initialized
            if not hasattr(app, 'bot'):
                return DiagnosticResult(
                    component="Bot Initialization",
                    status="ERROR",
                    message="Bot object not found in application"
                )
            
            # Initialize bot to get username
            try:
                await app.initialize()
                bot_username = app.bot.username
                await app.shutdown()
            except Exception as init_error:
                # Bot exists but not initialized yet - this is OK
                bot_username = "not_initialized"
            
            return DiagnosticResult(
                component="Bot Initialization",
                status="OK",
                message="Bot application created successfully",
                details={
                    "bot_username": bot_username,
                    "has_updater": hasattr(app, 'updater'),
                    "has_bot": hasattr(app, 'bot')
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="Bot Initialization",
                status="ERROR",
                message=f"Failed to initialize: {str(e)[:100]}",
                details={"error": str(e)}
            )
    
    async def check_handlers(self) -> DiagnosticResult:
        """Check handlers registration."""
        print("🔍 Checking handlers registration...")
        
        try:
            from app.bot import get_application
            
            app = get_application()
            
            if app is None:
                return DiagnosticResult(
                    component="Handlers Registration",
                    status="ERROR",
                    message="Cannot check handlers - bot not initialized"
                )
            
            # Count handlers
            handler_count = len(app.handlers)
            
            if handler_count == 0:
                return DiagnosticResult(
                    component="Handlers Registration",
                    status="ERROR",
                    message="No handlers registered"
                )
            
            # Expected handlers
            expected_commands = [
                "start", "help", "profile", "tasks", 
                "finances", "mood", "reminders", "sleep", "wake"
            ]
            
            return DiagnosticResult(
                component="Handlers Registration",
                status="OK",
                message=f"{handler_count} handlers registered",
                details={
                    "total_handlers": handler_count,
                    "expected_commands": expected_commands
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="Handlers Registration",
                status="ERROR",
                message=f"Failed to check handlers: {str(e)[:100]}",
                details={"error": str(e)}
            )
    
    async def check_ai_service(self) -> DiagnosticResult:
        """Check AI service availability."""
        print("🔍 Checking AI service...")
        
        try:
            from app.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            
            if not ai_service.available:
                return DiagnosticResult(
                    component="AI Service",
                    status="WARNING",
                    message="AI service not available (will use fallback responses)"
                )
            
            # Try a simple test
            try:
                response = await ai_service.generate_response(
                    user_message="test",
                    conversation_context=[]
                )
                
                if response:
                    return DiagnosticResult(
                        component="AI Service",
                        status="OK",
                        message="AI service responding correctly",
                        details={"test_response_length": len(response)}
                    )
            except Exception as test_error:
                return DiagnosticResult(
                    component="AI Service",
                    status="WARNING",
                    message=f"AI service available but test failed: {str(test_error)[:50]}"
                )
            
            return DiagnosticResult(
                component="AI Service",
                status="OK",
                message="AI service initialized"
            )
            
        except Exception as e:
            return DiagnosticResult(
                component="AI Service",
                status="WARNING",
                message=f"AI service check failed: {str(e)[:100]}",
                details={"error": str(e)}
            )
    
    async def run_full_diagnostic(self) -> DiagnosticReport:
        """Run full system diagnostic."""
        print("\n" + "="*60)
        print("🔬 MISIX System Diagnostics")
        print("="*60 + "\n")
        
        # Run all checks
        checks = [
            self.check_environment(),
            self.check_database(),
            self.check_database_schema(),
            self.check_bot_initialization(),
            self.check_handlers(),
            self.check_ai_service()
        ]
        
        self.results = await asyncio.gather(*checks)
        
        # Determine overall status
        error_count = sum(1 for r in self.results if r.status == "ERROR")
        warning_count = sum(1 for r in self.results if r.status == "WARNING")
        
        if error_count > 0:
            overall_status = "CRITICAL"
        elif warning_count > 0:
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"
        
        # Generate recommendations
        self.recommendations = self._generate_recommendations()
        
        report = DiagnosticReport(
            results=self.results,
            overall_status=overall_status,
            recommendations=self.recommendations
        )
        
        # Print results
        print("\n" + "="*60)
        print("📊 Results")
        print("="*60 + "\n")
        
        for result in self.results:
            print(result)
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, list):
                        print(f"  {key}: {', '.join(str(v) for v in value[:5])}")
                    else:
                        print(f"  {key}: {value}")
            print()
        
        print("="*60)
        print(f"Overall Status: {overall_status}")
        print("="*60)
        
        if self.recommendations:
            print("\n💡 Recommendations:\n")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"{i}. {rec}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []
        
        for result in self.results:
            if result.status == "ERROR":
                if result.component == "Environment Variables":
                    recommendations.append(
                        f"Set missing environment variables: {', '.join(result.details.get('missing', []))}"
                    )
                elif result.component == "Database Connection":
                    recommendations.append(
                        "Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file"
                    )
                elif result.component == "Database Schema":
                    recommendations.append(
                        f"Run migrations to create missing tables: {', '.join(result.details.get('missing', []))}"
                    )
                elif result.component == "Bot Initialization":
                    recommendations.append(
                        "Check TELEGRAM_BOT_TOKEN and bot initialization code"
                    )
                elif result.component == "Handlers Registration":
                    recommendations.append(
                        "Review bot/__init__.py to ensure all handlers are registered"
                    )
            
            elif result.status == "WARNING":
                if result.component == "AI Service":
                    recommendations.append(
                        "Check YANDEX_GPT_API_KEY and YANDEX_FOLDER_ID in .env file"
                    )
        
        if not recommendations:
            recommendations.append("System is healthy! No immediate actions needed.")
        
        return recommendations


async def main():
    """Main entry point."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Run diagnostics
        diagnostics = SystemDiagnostics()
        report = await diagnostics.run_full_diagnostic()
        
        # Save report
        report_path = Path(__file__).parent / "diagnostic_report.md"
        with open(report_path, "w") as f:
            f.write(report.to_markdown())
        
        print(f"\n📄 Full report saved to: {report_path}")
        
        # Exit with appropriate code
        if report.overall_status == "CRITICAL":
            sys.exit(1)
        elif report.overall_status == "DEGRADED":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
