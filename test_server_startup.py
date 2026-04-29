"""
Test if the server can start without errors (dry run)
"""
import sys

print("="*60)
print("SERVER STARTUP TEST")
print("="*60)

try:
    print("\n1. Testing imports...")
    from app.main import app
    print("   ✅ Main app imported")
    
    from app.api.routes import router
    print("   ✅ Routes imported")
    
    from app.core.config import settings
    print("   ✅ Config imported")
    
    print("\n2. Checking app configuration...")
    print(f"   Title: {app.title}")
    print(f"   Version: {app.version}")
    print(f"   Description: {app.description[:50]}...")
    
    print("\n3. Checking routes...")
    routes = [route for route in app.routes if hasattr(route, 'path')]
    for route in routes:
        if hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"   {methods:10} {route.path}")
    
    print("\n4. Checking environment config...")
    print(f"   Cortex Agent: {settings.cortex_agent_name}")
    print(f"   Cortex API Base: {settings.cortex_api_base}")
    print(f"   Pass Threshold: {settings.pass_threshold}")
    print(f"   Warn Threshold: {settings.warn_threshold}")
    
    print("\n5. Testing guidelines...")
    from app.evaluation.guidelines import get_guidelines
    guidelines = get_guidelines("rag agent")
    if guidelines:
        print(f"   ✅ RAG Agent guidelines loaded ({len(guidelines)} chars)")
    else:
        print("   ❌ RAG Agent guidelines NOT found")
        sys.exit(1)
    
    print("\n6. Testing schema validation...")
    from app.api.schemas import EvaluationRequest, ComponentPayload
    test_req = EvaluationRequest(
        user_query="Test query",
        components=[
            ComponentPayload(
                name="RAG Agent",
                input="Test input",
                output="Test output"
            )
        ]
    )
    print(f"   ✅ Request schema validation works")
    print(f"   Query ID: {test_req.query_id or 'auto-generated'}")
    print(f"   Components: {len(test_req.components)}")
    
    print("\n" + "="*60)
    print("✅ SERVER STARTUP TEST PASSED")
    print("="*60)
    print("\nThe server should start without errors.")
    print("Run: .\\venv\\Scripts\\activate.ps1; py run.py")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
