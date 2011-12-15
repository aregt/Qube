'''
After Effects renderTalk Scripts
Library of scripts that renderTalk uses
'''

def getOpenProjectScript(projectFile):
    name = "Open Project"
    script = '''\
try {
    app.openFast(File("%s"));
    "Project Loaded"
} catch(error) {
    this.log_file.writeln("ERROR: Unable to open project.\n" + error)
}
''' % str(projectFile)
    return prepScript(name, script)

def getRenderAllScript():
    name = "Render"
    script = '''\
try {
    if (app.preferences.havePref("Misc Section", "Play sound when render finishes")) {
    	saved_sound_setting = app.preferences.getPrefAsLong("Misc Section", "Play sound when render finishes");
    } else {
    	saved_sound_setting = 1;
    }
    app.preferences.savePrefAsLong("Misc Section", "Play sound when render finishes", 0);
    app.project.renderQueue.render();
    app.preferences.savePrefAsLong("Misc Section", "Play sound when render finishes", saved_sound_setting);
    "Project Rendered";
} catch(error) {
    this.log_file.writeln("ERROR: Unable to render.\n" + error);
    "ERROR";
}
'''
    return prepScript(name, script)

def getSetupSegmentScript(startFrame, endFrame, rqIndex):
    name = "Setup Segment"
    script = '''\
// Setup the render queue
var startFrame = %s;
var endFrame = %s;
var rqIndex = %s;

app.beginUndoGroup("Setup RenderQueue for render");
var errors = [];
// Make sure the rqItem exists
try {
    var rqItem = app.project.renderQueue.item(rqIndex);
} catch (error) {
    errors.push("Render Queue item doesn't exist: " + rqIndex);
};

// Check for problematic render queue item statuses
if (errors.length == 0) {
    if (rqItem.status == RQItemStatus.DONE) {
        errors.push("Render Queue item status is done. Needs to be queued.");
    } else if (rqItem.status == RQItemStatus.NEEDS_OUTPUT) {
        errors.push("Render Queue item needs output.");
    } else if (rqItem.status == RQItemStatus.USER_STOPPED) {
        errors.push("Render Queue item status is user stopped. Needs to be queued.");
    } else if (rqItem.status == RQItemStatus.ERR_STOPPED) {
        errors.push("Render Queue item status is error stopped. Needs to be queued.");
    };
};

// Set up the start and end frames
var start_time = rqItem.timeSpanStart;
var end_time   = rqItem.timeSpanStart + rqItem.timeSpanDuration;
var compStartFrame = rqItem.comp.displayStartTime / rqItem.comp.frameDuration;
var compEndFrame = rqItem.comp.duration / rqItem.comp.frameDuration - 1;
if (startFrame) {
    if (startFrame < compStartFrame || startFrame > compEndFrame) {
        errors.push("Start Frame (" + startFrame + ") out of range (" + compStartFrame + "-" + compEndFrame + ")");
    };
    start_time = -rqItem.comp.displayStartTime + ((parseInt(startFrame,10) - app.project.displayStartFrame) * rqItem.comp.frameDuration);
};
if (endFrame) {
    if (endFrame < compStartFrame || endFrame > compEndFrame) {
        errors.push("End Frame (" + endFrame + ") out of range (" + compStartFrame + "-" + compEndFrame + ")");
    };
    var end_frame_plus_one = parseInt(endFrame,10) + 1.0 - app.project.displayStartFrame;
    end_time = -rqItem.comp.displayStartTime + (end_frame_plus_one * rqItem.comp.frameDuration);
};

if (errors.length == 0) {
    // Turn off all other rq items
    for (var r=1; r<=app.project.renderQueue.numItems; r++) {
        try {
            app.project.renderQueue.item(r).render = false;
        } catch (error) {
            continue;
        };
    };

    // If the rq index has already been rendered once, create a duplicate to render from.
    var origRQItem = rqItem;
    rqItem = origRQItem.duplicate();
    origRQItem.render = false;

    // Make sure the output files are still the same
    for (var o=1; o<=origRQItem.outputModules.length; o++) {
        // Prefix the output file path of the original because multiple rq items can't have the same output file.
        outputFile = origRQItem.outputModule(o).file;
        if (outputFile.fsName.substr(0, 5) == "/RNDR") {
            outputFile = new File(outputFile.fsName.slice(5));
        } else {
            origRQItem.outputModule(o).file = new File("/RNDR" + outputFile.fsName);
        }
        rqItem.outputModule(o).file = outputFile;
    }
    rqItem.render = true;
    origRQItem.render = false;
    rqItem.logType = LogType.ERRORS_AND_PER_FRAME_INFO;
}; 

if (errors.length == 0) {
    rqItem.timeSpanStart = start_time;
    rqItem.timeSpanDuration = end_time - start_time;
    outputs = [];
    for (var o=1; o<=rqItem.outputModules.length; o++) {
        outputs.push(rqItem.outputModule(o).file.fsName);
    };
};
app.endUndoGroup();

if (errors.length > 0) {
    for (var e=0; e<errors.length; e++) {
        this.log_file.writeln("ERROR: " + errors[e]);
    };
    "ERROR";
} else { 
    outputs.toString();
};
''' % (startFrame, endFrame, rqIndex)

    return prepScript(name, script)

def getMultProcsScript(enable=True):
    name = "Setup Multiple Processors"
    script = '''\
switch (parseFloat(app.version)) {
    case 8:
        app.preferences.savePrefAsLong("MP", "Enable MP", %s);
        break;
    case 9:
        app.preferences.savePrefAsLong("New MP", "Enable MP", %s);
        break;
    case 10: case 10.5:
        app.preferences.savePrefAsLong("MP - CS5 - 4", "MP - Enable", %s);
        break;
};
app.preferences.saveToDisk();
true;
'''
    if enable:
        script = script % (1,1,1)
    else:
        script = script % (0,0,0)
    return prepScript(name, script)

def prepScript(name, script):
    '''
    Remove comments and make the script one line
    so it can be sent through the socket.
    Return a dictionary containing the name and the script.
    '''
    resultScript = []
    lines = script.split("\n")
    for line in lines:
        if not line.strip().startswith("//"):
            resultScript.append(line)
    
    resultScript = "".join(resultScript)
    
    result = {'name':name, 'script':resultScript}
    return result