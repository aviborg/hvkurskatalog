import pool from './config/db.js';

const checkCounts = async () => {
    try {
        const events = await pool.query('SELECT count(*) FROM course_events');
        const templates = await pool.query('SELECT count(*) FROM course_templates');
        console.log(`Events in DB: ${events.rows[0].count}`);
        console.log(`Templates in DB: ${templates.rows[0].count}`);
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await pool.end();
    }
};

checkCounts();
