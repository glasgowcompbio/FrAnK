Ext.define('metExploreViz.view.menu.viz_MiningMenu.Viz_MiningMenuModel', {
    extend: 'Ext.app.ViewModel',

   /* requires:['metexplore.model.d3.Network',
    'metexplore.model.d3.LinkReactionMetabolite'],
*/
    alias: 'viewmodel.menu-vizMiningMenu-vizMiningMenu',

    parent:'graphPanel',
    data: {
        name: 'metExploreViz'
    }

    /*stores:{
    	d3network:{
            model:'metexplore.model.d3.Network',
            autoLoad:false
        },
        linkReactionMetab:{
            model:'metexplore.model.d3.LinkReactionMetabolite',
            autoLoad:false
        }
    }*/

});
