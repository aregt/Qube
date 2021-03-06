#!/usr/bin/python

"""
Submit After Effects
Author: Brennan Chapman
Date: 5/19/2011

Purpose:
    Provide streamlined access
    to the aerender tool and report
    the status of the render to the
    user and Qube.

Features:
    Reports Progress to qube (1-100%)
    Dynamic Allocation
"""

import os, sys
import inspect
import logging
sys.path.append('/Applications/pfx/qube/api/python/')
import qb

# Gotta be a better way to do this.  Suggestions?
sys.path.insert(0, os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
print 'PATH: ' + str(sys.path)
import Job
import Render
import signal

# ---------------------------------------------------------------------------
# Set up the logger module
# ---------------------------------------------------------------------------

# Create logger
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# Create a formatter
formatter = logging.Formatter("%(levelname)s: %(message)s")
ch.setFormatter(formatter)
# Add ch to logger
logger.addHandler(ch)



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Global variable for render controller.  Used so cleanup method can access it.
render = None

# If on mac, cleanup extra aerendercore processes if job is killed early
def cleanup(signum, frame):
    # If we have a render class
    if render:
        render.killAERenderCoreProcesses()

if (os.uname()[0].lower() == 'darwin'):
    signal.signal(signal.SIGTERM, cleanup)

def initJob():
    # Get the job object
    jobObject = qb.jobobj()

    job = Job.Job(logger) # Create our own Job Object
    job.loadOptions(jobObject) # Load the Qube Job into our job template

    return job


def executeJob(job):
    global render
    jobstate = 'complete'

    # Run the job independently of the subjobs.
    # We will update the subjobs based on frames completed
    render = Render.Render(job)
    render.startRender()

    return jobstate


def cleanupJob(job, state):
    # jobObject = job.qubejob
    qb.reportjob(state)


def main():
    job      = initJob()
    state    = executeJob(job)
    cleanupJob(job, state)
    
if __name__ == "__main__":
    main()