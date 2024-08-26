from supabase import create_client, Client

url = "https://omqkgmymtquvyhyuyxqk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9tcWtnbXltdHF1dnloeXV5eHFrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ2OTA4MDksImV4cCI6MjA0MDI2NjgwOX0.vloUFDaAF81ILhZYnv49Kqn5JrBL9R39MQya2Q464DY"

supabase: Client = create_client(url, key)
