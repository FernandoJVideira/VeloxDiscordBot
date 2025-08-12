# PostgreSQL Migration Guide for UmbreonBot2

This guide will help you migrate your Discord bot from SQLite to PostgreSQL.

## Prerequisites

- Python 3.8+ with pip
- Docker (recommended) or PostgreSQL server
- Your existing bot files and environment

## Step 1: Set Up PostgreSQL Database

### Option A: Using Docker (Recommended)

1. Install Docker if you haven't already
2. Run PostgreSQL container:
```bash
docker run --name umbreon-postgres \
  -e POSTGRES_USER=umbreon \
  -e POSTGRES_PASSWORD=umbreon_pwd \
  -e POSTGRES_DB=umbreon \
  -p 5432:5432 \
  -d postgres:16
```

3. Verify the container is running:
```bash
docker ps
```

### Option B: Local PostgreSQL Installation

1. Install PostgreSQL on your system
2. Create a database and user:
```sql
CREATE DATABASE umbreon;
CREATE USER umbreon WITH PASSWORD 'umbreon_pwd';
GRANT ALL PRIVILEGES ON DATABASE umbreon TO umbreon;
```

## Step 2: Install Dependencies

Install the PostgreSQL adapter:
```bash
pip install -r requirements.txt
```

The updated `requirements.txt` now includes `psycopg2-binary`.

## Step 3: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example vars.env
```

2. Edit `vars.env` with your settings:
```env
# Discord Bot Configuration
TOKEN=your_discord_bot_token_here
APPLICATION_ID=your_discord_application_id_here

# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=umbreon
POSTGRES_USER=umbreon
POSTGRES_PASSWORD=umbreon_pwd
```

**⚠️ Important: Never commit your `vars.env` file to version control!**

## Step 4: Initialize the Database Schema

The new PostgreSQL schema will be automatically created when you first run the bot. The schema includes:

- Proper primary keys for data integrity
- BIGINT for Discord snowflakes (user/guild/channel IDs)
- BOOLEAN columns instead of INTEGER
- Performance indexes for common queries

## Step 5: Migrate Existing Data (Optional)

If you have existing SQLite data you want to keep:

1. Make sure your old `bot.db` file is in the project directory
2. Run the migration script:
```bash
python migrate_sqlite_to_postgres.py
```

This script will:
- Copy all existing data from SQLite to PostgreSQL
- Handle data type conversions (booleans, IDs)
- Skip duplicate entries safely
- Provide detailed progress output

**Note: If you're starting fresh, you can skip this step.**

## Step 6: Test the Migration

1. Start your bot:
```bash
python bot.py
```

2. Look for these success messages:
```
✅ Database connection established successfully
🔧 Loading extensions...
✅ Loaded cogs.Commands.Sync
...
🤖 Your Bot is ready and connected to PostgreSQL!
```

3. Test basic functionality:
   - Try a level system command (if enabled)
   - Test the welcome system
   - Check RPS game functionality

## Key Changes Made

### Database Handler
- Replaced SQLite-specific code with PostgreSQL connection pooling
- Added automatic `?` to `%s` placeholder conversion for compatibility
- Removed SQLite-specific retry logic for "database is locked"
- Added proper error handling and connection management

### Schema Improvements
- Added primary keys to all tables
- Changed boolean columns from INTEGER to BOOLEAN
- Used BIGINT for Discord IDs (handles large snowflake values)
- Added performance indexes for common queries

### Architecture
- Centralized database handler (one instance shared across all cogs)
- Maintained backward compatibility with existing query syntax
- Improved error reporting and connection management

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to database"**
- Verify PostgreSQL is running: `docker ps` (if using Docker)
- Check environment variables in `vars.env`
- Ensure the database exists and credentials are correct

**Error: "Connection refused"**
- PostgreSQL might not be running
- Check if port 5432 is available: `netstat -ln | grep 5432`
- Verify firewall settings

### Migration Issues

**Error: "SQLite database 'bot.db' not found"**
- This is normal if you don't have existing data
- You can skip the migration step and start fresh

**Error: "Permission denied for database"**
- Check database user permissions
- Ensure the user has CREATE, INSERT, UPDATE, DELETE privileges

### Performance Issues

**Slow query performance**
- The new schema includes indexes for common queries
- Monitor query performance and add indexes if needed
- Consider using EXPLAIN ANALYZE for slow queries

## Production Deployment

### Security Considerations

1. **Environment Variables**: Use a secure secret management system
2. **Database Credentials**: Use strong, unique passwords
3. **Network Security**: Restrict database access to your application only
4. **SSL/TLS**: Enable SSL for database connections in production

### Recommended Production Setup

```env
# Production environment variables
POSTGRES_HOST=your-postgres-host.com
POSTGRES_PORT=5432
POSTGRES_DB=umbreon_prod
POSTGRES_USER=umbreon_prod
POSTGRES_PASSWORD=very_secure_password_here
POSTGRES_SSLMODE=require
```

### Backup Strategy

1. **Regular Backups**:
```bash
pg_dump -h localhost -U umbreon -d umbreon > backup_$(date +%Y%m%d_%H%M%S).sql
```

2. **Automated Backups**: Set up cron jobs or use your hosting provider's backup service

## Performance Monitoring

### Key Metrics to Monitor
- Connection pool usage
- Query execution times
- Database size growth
- Index usage statistics

### Useful PostgreSQL Queries
```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'umbreon';

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public';

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

## Future Improvements

### Async Migration (Optional)
For better performance in high-traffic bots, consider migrating to async database operations:
- Replace `psycopg2` with `asyncpg`
- Convert all database methods to `async def`
- Update all call sites to use `await`

### Query Optimization
- Replace SELECT-then-INSERT/UPDATE patterns with PostgreSQL UPSERT
- Use prepared statements for frequently executed queries
- Implement query result caching where appropriate

## Need Help?

If you encounter issues:
1. Check the console output for detailed error messages
2. Verify your environment configuration
3. Test database connectivity independently
4. Review PostgreSQL logs for server-side issues

The migration maintains full backward compatibility with your existing code while providing better performance, reliability, and data integrity.