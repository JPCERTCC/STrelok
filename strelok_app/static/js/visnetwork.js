function visNetwork(nodes, edges, icon){
    var container = document.getElementById('network');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = visOption();
    if (icon==true){
        options = useIcon(options);
    }
    var network = new vis.Network(container, data, options);
    network.on("doubleClick", function (params) {
        var object = network.getSelectedNodes();
        //models = types;
        models = [
            "attack-pattern", 
            "campaign",
            "course-of-action",
            "identity",
            "indicator",
            "intrusion-set",
            "malware", 
            "threat-actor", 
            "tool", 
            "vulnerability", 
        ];
        if (models.includes(object[0])){
            location.href = "/stix/" + object;
        }
    });
    return network;
};

function useIcon(options){
    options.groups = {
        "malware":{ shape: 'image', image:'/static/icons/stix2_malware_icon_tiny_round_v1.png' },
        "tool":{ shape: 'image', image:'/static/icons/stix2_tool_icon_tiny_round_v1.png' },
        "vulnerability":{ shape: 'image', image:'/static/icons/stix2_vulnerability_icon_tiny_round_v1.png' },
        "identity":{ shape: 'image', image:'/static/icons/stix2_identity_icon_tiny_round_v1.png' },
        "indicator":{ shape: 'image', image:'/static/icons/stix2_indicator_icon_tiny_round_v1.png' },
        "campaign":{ shape: 'image', image:'/static/icons/stix2_campaign_icon_tiny_round_v1.png' },
        "threat-actor":{ shape: 'image', image:'/static/icons/stix2_threat_actor_icon_tiny_round_v1.png' },
        "attack-pattern":{ shape: 'image', image:'/static/icons/stix2_attack_pattern_icon_tiny_round_v1.png' },
        "intrusion-set":{ shape: 'image', image:'/static/icons/stix2_intrusion_set_icon_tiny_round_v1.png' },
        "course-of-action":{ shape: 'image', image:'/static/icons/stix2_course_of_action_icon_tiny_round_v1.png' },
    }
    return options;
}

function visOption(){

    var options ={
        "autoResize": true,
        "configure": {
                "enabled": false,
                //"filter": 'nodes,edges',
                //"showButton": true
        },
        "nodes": {
                "borderWidth": 0.1,
                "scaling":{
                        "label": {
                                "enabled": true,
                        },
                },
                "shadow": true,
                "color":{
                    "background":"white",
                },
                "physics":true,
        },
        "groups":{
            "Organization":{
                shape: 'icon',
                icon:{
                    code:'\uf1ad',
                    color:'green',
                },
                color:'green',
            },
        },
        "edges":{
                "arrows": 'to',
                "scaling":{
                        "label": {
                                "enabled": true,
                        },
                },
                "shadow": true,
                "smooth": {
                        //"roundness": 0.1
                },
                "width":2,
                //"physics":false,
        },
        "interaction":{
                "hideEdgesOnDrag": false,
                "hover": false,
                "keyboard": true,
                "navigationButtons": true,
        },
        "physics": {
                enabled: true,
                "solver": "forceAtlas2Based",
                //"solver": "barnesHut",
                //"solver": "repulsion",
                barnesHut: {
                    gravitationalConstant:-2000,
                    centralGravity:0.4,
                    springLength: 150,
                    //springConstant: 0.02,
                    //damping: 0.1,
                    avoidOverlap: 0.1,
                },
                repulsion: {
                    nodeDistance: 150,
                    centralGravity:0.5,
                    springLength: 100,
                },
                forceAtlas2Based:{  
                    gravitationalConstant:-50,
                    centralGravity:0.01,
                    springLength:150,
                    avoidOverlap:0.1,
                },
                "minVelocity":5,
        },
        "manipulation": {
              "enabled": false,
        },
    };
    return options;
};
