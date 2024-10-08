-- Create an index for faster querying of recently updated jobs
CREATE INDEX idx_job_details_last_updated_at ON job_details(last_updated_at);

-- Ensure last_updated_at is updated automatically on row updates
CREATE OR REPLACE FUNCTION update_last_updated_at_job_details()
RETURNS TRIGGER AS $$
BEGIN
   NEW.last_updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update last_updated_at for job_details
CREATE TRIGGER update_last_updated_at_job_details
BEFORE UPDATE ON job_details
FOR EACH ROW
EXECUTE FUNCTION update_last_updated_at_job_details();

-- Policy to allow users to SELECT only their own jobs based on application-level user_id
CREATE POLICY select_own_jobs_policy
ON job_details
FOR SELECT
USING (user_id = current_setting('myapp.user_id')::INTEGER);

-- Policy to allow users to INSERT jobs only for themselves
CREATE POLICY insert_own_jobs_policy
ON job_details
FOR INSERT
WITH CHECK (user_id = current_setting('myapp.user_id')::INTEGER);

-- Policy to allow users to UPDATE only their own jobs
CREATE POLICY update_own_jobs_policy
ON job_details
FOR UPDATE
USING (user_id = current_setting('myapp.user_id')::INTEGER)
WITH CHECK (user_id = current_setting('myapp.user_id')::INTEGER);

-- Policy to allow users to DELETE only their own jobs
CREATE POLICY delete_own_jobs_policy
ON job_details
FOR DELETE
USING (user_id = current_setting('myapp.user_id')::INTEGER);

-- Force Row-Level Security to be applied to all users, even superusers
ALTER TABLE job_details FORCE ROW LEVEL SECURITY;


-- Ensure last_updated_at is updated automatically on row updates
CREATE OR REPLACE FUNCTION update_last_updated_at_processed_emails()
RETURNS TRIGGER AS $$
BEGIN
   NEW.last_updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;
