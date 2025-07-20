from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Check database connection and configuration'
    
    def handle(self, *args, **options):
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database connection successful!')
            )
            self.stdout.write(f'Database: {settings.DATABASES["default"]["NAME"]}')
            self.stdout.write(f'Host: {settings.DATABASES["default"]["HOST"]}')
            self.stdout.write(f'Port: {settings.DATABASES["default"]["PORT"]}')
            self.stdout.write(f'PostgreSQL Version: {version}')
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                self.stdout.write(f'\n📋 Found {len(tables)} tables:')
                for table in tables:
                    self.stdout.write(f'  - {table[0]}')
            else:
                self.stdout.write(
                    self.style.WARNING('\n⚠️  No tables found. Run migrations first.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {str(e)}')
            )
            self.stdout.write('\nTroubleshooting steps:')
            self.stdout.write('1. Ensure PostgreSQL is running on port 5433')
            self.stdout.write('2. Check database credentials in .env file')
            self.stdout.write('3. Create database if it doesn\'t exist:')
            self.stdout.write('   createdb -p 5433 -U postgres shopfusion_db')
