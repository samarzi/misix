#!/bin/bash
# Setup Supabase CLI connection

echo "🔧 Setting up Supabase CLI connection"
echo "======================================"
echo ""

# Your Supabase project details
PROJECT_REF="dcxdnrealygulikpuicm"
SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjeGRucmVhbHlndWxpa3B1aWNtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQ1NzA4MCwiZXhwIjoyMDc4MDMzMDgwfQ.y4BIJVvw4djQs9xWLo1Ff8rC3W-vPWhvlIhHgLqlvqg"

echo "Project Reference: ${PROJECT_REF}"
echo "Service Key: ${SERVICE_KEY:0:20}..."
echo ""

# Link to Supabase project
echo "📡 Linking to Supabase project..."
supabase link --project-ref ${PROJECT_REF}

echo ""
echo "✅ Setup complete!"
echo ""
echo "Now you can use Supabase CLI commands:"
echo "  supabase db push          # Push migrations"
echo "  supabase db pull          # Pull schema"
echo "  supabase db reset         # Reset database"
echo "  supabase migration list   # List migrations"
echo ""
