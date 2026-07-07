export const portal={name:"NovaRide Dispatch",role:"dispatcher",features:["Live Rides Map","Dispatch Queue","Driver Lookup","Fare Review","City Operations","Safety Monitoring","Replay Verification","Performance Analytics"]} as const;
export const assignDriver=(rideId:string,driverId:string)=>({rideId,driverId,decision:"assigned",auditEvent:"dispatch.assignment"});
export const render=()=>`<main aria-label="${portal.name}"><h1>${portal.name}</h1>${portal.features.map(feature=>`<button aria-label="Open ${feature}">${feature}</button>`).join("")}</main>`;
