export const curatorStatsEvent = new Event("curatorStatsUpdate");

export function updateCuratorStats(){
    window.dispatchEvent(curatorStatsEvent);
}