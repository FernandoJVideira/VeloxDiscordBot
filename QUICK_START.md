# Quick Start Guide - PostgreSQL Migration Complete! 🎉

Your Discord bot has been successfully migrated from SQLite to PostgreSQL. Here's how to get it running:

## ✅ What's Been Fixed

The migration is **COMPLETE** and all code issues have been resolved:

- ✅ PostgreSQL DatabaseHandler with connection pooling
- ✅ All cogs updated to use shared database instance  
- ✅ Automatic `?` to `%s` placeholder conversion (no query changes needed)
- ✅ Import errors fixed (`EventUtils`, `Logger`)
- ✅ Type annotation compatibility issues resolved
- ✅ Environment variable validation added
- ✅ Proper error handling and logging

## 🚀 Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up PostgreSQL

**Option A: Docker (Recommended)**
```bash
docker run --name umbreon-postgres \
  -e POSTGRES_USER=umbreon \
  -e POSTGRES_PASSWORD=umbreon_pwd \
  -e POSTGRES_DB=umbreon \
  -p 5432:5432 \
  -d postgres:16
```

**Option B: Local PostgreSQL**
- Install PostgreSQL on your system
- Create database `umbreon` with user `umbreon`

### Step 3: Configure Environment
```bash
# Copy the example file
cp .env.example vars.env

# Edit vars.env with your settings:
TOKEN=your_discord_bot_token
APPLICATION_ID=your_discord_application_id
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=umbreon
POSTGRES_USER=umbreon
POSTGRES_PASSWORD=umbreon_pwd
```

### Step 4: Migrate Existing Data (Optional)
If you have existing SQLite data:
```bash
python migrate_sqlite_to_postgres.py
```

### Step 5: Start the Bot
```bash
python bot.py
```

You should see:
```
✅ Database connection established successfully
🔧 Loading extensions...
✅ Loaded cogs.Commands.Sync
✅ Loaded cogs.Events.EventHandler
...
🤖 VeloxBot is ready and connected to PostgreSQL!
📊 Serving X guilds
```

## 🎯 Key Improvements

### Performance & Reliability
- **Connection Pooling**: Efficient database connections
- **No More Locks**: Eliminated "database is locked" errors
- **Better Error Handling**: Clear error messages and graceful failures
- **Scalability**: Can handle multiple bot instances

### Data Integrity
- **Primary Keys**: All tables now have proper primary keys
- **Data Types**: BIGINT for Discord IDs, BOOLEAN for flags
- **Constraints**: Better data validation and relationships

### Developer Experience
- **Centralized DB**: Single database instance shared across all cogs
- **Backward Compatible**: All existing queries work unchanged
- **Better Logging**: Detailed startup and error information

## 🛠 Troubleshooting

### "Failed to connect to database"
- Check if PostgreSQL is running: `docker ps`
- Verify environment variables in `vars.env`
- Test connection: `psql -h localhost -U umbreon -d umbreon`

### "Extension failed to load"
- Check console output for specific error
- Ensure all dependencies are installed
- Verify Python version compatibility

### Migration Issues
- SQLite file not found: Normal if starting fresh
- Permission errors: Check PostgreSQL user privileges
- Data conflicts: Migration script handles duplicates automatically

## 📊 Monitoring & Maintenance

### Check Database Status
```sql
-- Connect to PostgreSQL
psql -h localhost -U umbreon -d umbreon

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public';

-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'umbreon';
```

### Backup Your Data
```bash
# Create backup
pg_dump -h localhost -U umbreon -d umbreon > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U umbreon -d umbreon < backup_20231201.sql
```

## 🔧 Advanced Configuration

### Production Environment
For production deployments, consider:
- Using managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- Setting up SSL connections (`POSTGRES_SSLMODE=require`)
- Implementing connection pooling with PgBouncer
- Regular automated backups

### Performance Tuning
- Monitor slow queries with `EXPLAIN ANALYZE`
- Add indexes for frequently queried columns
- Consider read replicas for high-traffic bots

## 🎉 You're All Set!

Your bot is now running on PostgreSQL with improved performance, reliability, and scalability. The migration maintains full backward compatibility while providing enterprise-grade database features.

For detailed information, see:
- `POSTGRES_MIGRATION.md` - Comprehensive migration guide
- `bot_postgres_schema.sql` - Database schema
- `migrate_sqlite_to_postgres.py` - Data migration script

**Happy coding! 🤖✨**